from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from market.models import (
    GoodsModel,
    GroupOfGoods,
    ProductBrand,
    ProductBrandI18n,
    ProductContent,
    ProductContentAgentSettings,
)
from market.product_content import apply_product_content
from market.product_content_prompt import extra_sites_for_text, official_site_for_text
from market.product_content_agent import (
    AgentConfigError,
    AgentRunError,
    accept_agent_draft,
    extract_json_object,
    pending_enrichment_queryset,
    run_content_agent,
    save_agent_draft,
)


class AgentJsonTests(TestCase):
    def test_extracts_fenced_json(self):
        payload = extract_json_object('note\n```json\n{"brand_name": "O HUI", "blocks": []}\n```')
        self.assertEqual(payload["brand_name"], "O HUI")

    def test_extracts_nested_fenced_json(self):
        payload = extract_json_object(
            '```json\n{"brand_name": "O HUI", "blocks": [{"kind": "lead", "body": "x"}]}\n```'
        )
        self.assertEqual(payload["blocks"][0]["kind"], "lead")

    def test_repairs_trailing_comma(self):
        payload = extract_json_object('{"brand_name": "O HUI", "blocks": [],}')
        self.assertEqual(payload["brand_name"], "O HUI")

    def test_repairs_inci_quotes_and_missing_commas(self):
        payload = extract_json_object(
            '{"brand_name":"","blocks":[{"kind":"ingredients","body":"","items":['
            '{"name": "Ganoderma Lucidum ("Mushroom") Extract", "text": ""}\n'
            '{"name": "Angelica Acutiloba Root Extract", "text": ""}'
            '],"source_url":"https://a.test"}]}'
        )
        names = [item["name"] for item in payload["blocks"][0]["items"]]
        self.assertIn("Mushroom", names[0])
        self.assertIn("Angelica", names[1])

    def test_curacion_maps_to_91cosmedi(self):
        self.assertEqual(
            official_site_for_text("Curación LACTO AQUANIC CREAM MASK"),
            "https://91cosmedi.com/en/curacion/",
        )

    def test_whoo_detail_slugs(self):
        from market.product_content_agent import WHOO_PREFIXES, _detail_slugs

        slugs = _detail_slugs(
            "The History of Whoo Hwanyu Imperial Youth Emulsion (BOX 18) (530 g)",
            WHOO_PREFIXES,
        )
        self.assertIn("imperial-youth-emulsion", slugs)
        self.assertIn("hwanyu-imperial-youth-emulsion", slugs)
        self.assertEqual(
            official_site_for_text("The history of Whoo Two way Pact 01"),
            "https://whoo-hk.com/en/productdetail/",
        )
        self.assertEqual(
            extra_sites_for_text("The History of Whoo Hwanyu Imperial Youth Emulsion"),
            ["https://themonodist.com/"],
        )

    def test_allows_crlf_after_url_string(self):
        payload = extract_json_object(
            '{"brand_name":"","blocks":[{"kind":"lead","body":"x","items":[],'
            '"source_url":"https://www.hwahae.com/en/products/curaci%C3%B3n-MASK/1"\r\n }]}'
        )
        self.assertIn("hwahae.com", payload["blocks"][0]["source_url"])

    def test_splits_usage_out_of_about(self):
        from market.product_content_agent import _sanitize_draft

        draft = _sanitize_draft(
            {
                "brand_name": "",
                "blocks": [
                    {
                        "kind": "lead",
                        "body": "Маска успокаивает кожу.",
                        "items": [],
                        "source_url": "https://91cosmedi.com/en/curacion/",
                    },
                    {
                        "kind": "about",
                        "body": (
                            "Маска успокаивает кожу.\n"
                            "Крем можно использовать как маску.\n"
                            "Способ использования 1. Нанесите на лицо.\n"
                            "Способ использования 2. Оставьте на ночь."
                        ),
                        "items": [],
                        "source_url": "https://91cosmedi.com/en/curacion/",
                    },
                ],
            },
            brand_locked=True,
        )
        kinds = {block["kind"]: block for block in draft["blocks"]}
        self.assertNotIn("Маска успокаивает кожу.", kinds["about"]["body"])
        self.assertIn("how_to_use", kinds)
        self.assertEqual(len(kinds["how_to_use"]["items"]), 2)

    def test_splits_mixed_about_into_ingredients_and_usage(self):
        from market.product_content_agent import _sanitize_draft

        draft = _sanitize_draft(
            {
                "brand_name": "",
                "blocks": [
                    {
                        "kind": "about",
                        "body": (
                            "ACFIT V-SANG GEL\n"
                            "Содержит запатентованный ингредиент Soothing Cooler, а также экстракт звездчатого аниса.\n"
                            "Полученный из плодов растения звездчатый анис, помогает успокоить и стабилизировать кожу.\n"
                            "Содержит экстракт спарассиса курчавого (гриб) + бета-глюкан\n"
                            "Экстракт спарассиса курчавого (гриб) - Обеспечивает увлажнение, помогая успокоить кожу.\n"
                            "* Среди грибов наибольшее содержание бета-глюкана имеет спарассис курчавый.\n"
                            "Бета-глюкан (B-глюкан) - Он помогает поддерживать кожу увлажненной.\n"
                            "Содержит 5 видов гиалуроновой кислоты: Гиалуронат натрия. Вы почувствуете более глубокий увлажняющий эффект.\n"
                            "- В случае если ваша кожа была подвержена агрессивному воздействию внешних факторов, "
                            "то нанесите гель толстым слоем, оставьте на 15–20 минут."
                        ),
                        "items": [],
                        "source_url": "catalog:description",
                    }
                ],
            },
            brand_locked=True,
        )
        kinds = {block["kind"]: block for block in draft["blocks"]}
        self.assertIn("ingredients", kinds)
        names = " ".join(item["name"] for item in kinds["ingredients"]["items"])
        self.assertIn("Soothing Cooler", names)
        self.assertIn("гиалуроновой", names.casefold() + kinds["ingredients"]["items"][-1]["name"].casefold())
        self.assertIn("how_to_use", kinds)
        usage = " ".join(kinds["how_to_use"]["items"] or [kinds["how_to_use"]["body"]])
        self.assertIn("нанесите", usage.casefold())
        about_body = (kinds.get("about") or {}).get("body") or ""
        self.assertNotIn("нанесите гель толстым слоем", about_body.casefold())
        self.assertNotIn("Содержит 5 видов", about_body)

    def test_splits_benefits_joined_by_bullets(self):
        from market.product_content_agent import _sanitize_draft

        draft = _sanitize_draft(
            {
                "brand_name": "",
                "blocks": [
                    {
                        "kind": "benefits",
                        "body": "",
                        "items": [
                            "Глубокое увлажнение кожи• Успокоение и омоложение кожи",
                            "Укрепление естественной силы кожи• Мягкое и бережное очищение",
                            "Регулирование уровня pH и удаление омертвевших клеток",
                        ],
                        "source_url": "catalog:description",
                    }
                ],
            },
            brand_locked=True,
        )
        items = draft["blocks"][0]["items"]
        self.assertEqual(
            items,
            [
                "Глубокое увлажнение кожи",
                "Успокоение и омоложение кожи",
                "Укрепление естественной силы кожи",
                "Мягкое и бережное очищение",
                "Регулирование уровня pH и удаление омертвевших клеток",
            ],
        )

    def test_keeps_catalog_source(self):
        from market.product_content_agent import CATALOG_SOURCE, _sanitize_draft

        draft = _sanitize_draft(
            {
                "brand_name": "",
                "blocks": [
                    {
                        "kind": "lead",
                        "body": "из каталога",
                        "items": [],
                        "source_url": CATALOG_SOURCE,
                    }
                ],
            },
            brand_locked=True,
        )
        self.assertEqual(draft["blocks"][0]["body"], "из каталога")

    def test_geo_block_message(self):
        from unittest.mock import Mock

        from market.product_content_agent import _raise_openai_error

        response = Mock()
        response.status_code = 403
        response.text = '{"error":{"code":"unsupported_country_region_territory"}}'
        with self.assertRaises(AgentRunError) as raised:
            _raise_openai_error(response)
        self.assertIn("CONTENT_AGENT_PROXY", str(raised.exception))


class AgentDraftTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Наборы",
            updated="2024-01-01T00:00:00Z",
        )
        self.good = GoodsModel.objects.create(
            id=5010,
            title="O HUI The First Cushion Set",
            description="<p>Набор</p>",
            category=self.category,
            type="goods",
            stock=1,
            weight=80,
        )
        apply_product_content(self.good, force=True)
        ProductContentAgentSettings.load()
        ProductContentAgentSettings.objects.filter(pk=1).update(enabled=True, prompt="test")

    def test_accept_does_not_overwrite_existing_brand(self):
        brand = ProductBrand.objects.create(slug="ohui")
        ProductBrandI18n.objects.create(brand=brand, language="ru", name="O HUI")
        self.good.content_brand = brand
        self.good.save(update_fields=["content_brand"])
        content = self.good.pdp_content
        content.agent_draft = {
            "brand_name": "Wrong Brand",
            "blocks": [
                {
                    "kind": "set_contents",
                    "heading": "В набор входит",
                    "body": "",
                    "items": [{"name": "Cushion", "text": "15 г"}],
                    "source_url": "https://example.com/p",
                }
            ],
        }
        content.save(update_fields=["agent_draft"])
        accept_agent_draft(self.good)
        self.good.refresh_from_db()
        self.assertEqual(self.good.content_brand_id, brand.id)
        self.assertTrue(
            self.good.pdp_content.blocks.filter(kind="set_contents").exists()
        )

    def test_drops_blocks_without_source(self):
        from market.product_content_agent import _sanitize_draft

        draft = _sanitize_draft(
            {
                "brand_name": "O HUI",
                "blocks": [
                    {"kind": "lead", "body": "текст без ссылки", "items": [], "source_url": ""},
                    {
                        "kind": "about",
                        "body": "с источником",
                        "items": [],
                        "source_url": "https://ohui.com/x",
                    },
                ],
            },
            brand_locked=False,
        )
        self.assertEqual(len(draft["blocks"]), 1)
        self.assertEqual(draft["blocks"][0]["kind"], "about")

    @patch("market.product_content_agent.call_content_llm")
    def test_run_stores_draft(self, mocked):
        mocked.return_value = '{"brand_name": "O HUI", "blocks": [{"kind": "lead", "body": "лид", "items": [], "source_url": "https://ohui.com"}]}'
        draft = run_content_agent(self.good)
        self.assertEqual(draft["brand_name"], "O HUI")
        self.good.pdp_content.refresh_from_db()
        self.assertIsNotNone(self.good.pdp_content.agent_run_at)

    @patch("market.product_content_agent.call_content_llm")
    def test_empty_llm_uses_catalog_description(self, mocked):
        mocked.return_value = (
            '{"notes": "нет на сайте", "blocks": [], "brand_name": "Curación", '
            '"official_url": "https://91cosmedi.com/en/curacion/"}'
        )
        self.good.title = "CURACION Lacto Aquanic Cream Mask"
        self.good.description = (
            "<p>Крем увлажняет кожу.</p><p>Способ использования 1. Нанесите на лицо.</p>"
        )
        self.good.save(update_fields=["title", "description"])
        draft = run_content_agent(self.good)
        self.assertTrue(draft["blocks"])
        self.assertIn("каталога", draft["notes"])

    @patch("market.product_content_agent.call_content_llm")
    def test_bad_json_falls_back_to_catalog(self, mocked):
        mocked.return_value = '{"blocks":[{"kind":"ingredients","items":[{"name": "Ganoderma ("Mushroom") Extract"}]}'
        self.good.description = "<p>Крем увлажняет кожу.</p>"
        self.good.save(update_fields=["description"])
        draft = run_content_agent(self.good)
        self.assertTrue(draft["blocks"])
        ProductContentAgentSettings.objects.filter(pk=1).update(enabled=False)
        with self.assertRaises(AgentConfigError):
            run_content_agent(self.good)

    def test_pending_skips_already_run(self):
        save_agent_draft(self.good, {"blocks": []})
        self.assertFalse(pending_enrichment_queryset().filter(id=self.good.id).exists())

    def test_failed_run_stays_pending(self):
        save_agent_draft(self.good, None, error="Некорректный JSON", recorded=False)
        self.assertTrue(pending_enrichment_queryset().filter(id=self.good.id).exists())
        self.assertIsNone(self.good.pdp_content.agent_run_at)


class AgentAdminButtonTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "a@a.test", "pass")
        category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Наборы",
            updated="2024-01-01T00:00:00Z",
        )
        self.good = GoodsModel.objects.create(
            id=5011,
            title="Test",
            description="x",
            category=category,
            type="goods",
            stock=1,
        )

    def test_enrich_button_disabled_message(self):
        ProductContentAgentSettings.load()
        self.client.force_login(self.user)
        url = reverse("admin:market_goodsmodel_enrich_content", args=[self.good.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_goods_change_has_action_table(self):
        apply_product_content(self.good, force=True)
        self.client.force_login(self.user)
        url = reverse("admin:market_goodsmodel_change", args=[self.good.pk])
        response = self.client.get(url)
        self.assertContains(response, "Контент карточки")
        self.assertContains(response, "Запуск")
        self.assertContains(response, "Секции контента")

    def test_productcontent_search_by_title_does_not_500(self):
        apply_product_content(self.good, force=True)
        self.client.force_login(self.user)
        url = reverse("admin:market_productcontent_changelist")
        response = self.client.get(url, {"q": "The history of Whoo Two way Pact"})
        self.assertEqual(response.status_code, 200)

    def test_productcontent_change_has_sections_and_accept(self):
        apply_product_content(self.good, force=True)
        content = self.good.pdp_content
        content.agent_draft = {"blocks": [{"kind": "lead", "body": "x", "source_url": "https://a.test"}]}
        content.save(update_fields=["agent_draft"])
        self.client.force_login(self.user)
        url = reverse("admin:market_productcontent_change", args=[content.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Принять черновик")
