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

    def test_disabled_raises(self):
        ProductContentAgentSettings.objects.filter(pk=1).update(enabled=False)
        with self.assertRaises(AgentConfigError):
            run_content_agent(self.good)

    def test_pending_skips_already_run(self):
        save_agent_draft(self.good, {"blocks": []})
        self.assertFalse(pending_enrichment_queryset().filter(id=self.good.id).exists())


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
