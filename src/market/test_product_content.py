from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from market.models import (
    GoodsModel,
    GroupOfGoods,
    ProductContent,
    ProductContentBlockI18n,
)
from market.product_content import apply_product_content, parse_product_description, strip_html
from market.utils import BusinessRuService

from .tests import FakeGoodsClient, korea_payload

SAMPLE_TITLE = "23 Skin Lab. Derma Tension Peel Off Pack"
SAMPLE_HTML = """
<p>23 Skin Lab — это дерматологический корейский бренд, созданный с философией возвращения кожи к её самому здоровому состоянию.</p>
<p>В основе всех формул:</p>
<p>фирменные комплексы DERMA-CLERA™</p>
<p>23 Skin Lab. Derma Tension Peel Off Pack — это мягкая peel-off маска, созданная для укрепления кожи.</p>
<p>Преимущества:</p>
<p>Повышает упругость и тонус кожи</p>
<p>Снимает омертвевшие клетки кожи, делая её гладкой</p>
<p>Основные компоненты:</p>
<p>CICA Water Base — успокаивает раздражения</p>
<p>Low-Molecular Collagen — повышает эластичность</p>
<p>Текстура и финиш:</p>
<p>Мягкая гелевая текстура</p>
<p>Способ применения:</p>
<p>Нанесите равномерным слоем на очищенную кожу лица</p>
<p>Оставьте до полного высыхания</p>
<p>Подходит для:</p>
<p>Всех типов кожи, особенно для уставшей, обезвоженной и чувствительной.</p>
<p>Объём: 50 мл</p>
<p>Вес: 80 гр</p>
"""


class ProductContentParserTests(TestCase):
    def test_strips_html_tags(self):
        self.assertEqual(strip_html("<p>Абзац<br>ещё</p>"), "Абзац\nещё")

    def test_strips_emoji(self):
        self.assertEqual(
            strip_html("<p>обновление кожи 🌿</p><p>лифтинг ✨💧</p>"),
            "обновление кожи\nлифтинг",
        )

    def test_parses_sample_sections(self):
        parsed = parse_product_description(SAMPLE_TITLE, SAMPLE_HTML)
        kinds = [block["kind"] for block in parsed["blocks"]]
        self.assertEqual(parsed["brand_name"], "23 Skin Lab")
        self.assertEqual(parsed["kind_slug"], "mask")
        self.assertIn("lead", kinds)
        self.assertIn("about", kinds)
        self.assertIn("benefits", kinds)
        self.assertIn("ingredients", kinds)
        self.assertIn("texture", kinds)
        self.assertIn("how_to_use", kinds)
        self.assertIn("suitable_for", kinds)
        self.assertIn("volume", kinds)
        self.assertIn("weight", kinds)
        by_kind = {block["kind"]: block for block in parsed["blocks"]}
        self.assertIn("peel-off маска", by_kind["lead"]["body"])
        self.assertEqual(by_kind["volume"]["body"], "50 мл")
        self.assertEqual(by_kind["weight"]["body"], "80 гр")
        self.assertGreaterEqual(len(by_kind["benefits"]["items"]), 2)
        self.assertEqual(by_kind["ingredients"]["items"][0]["name"], "CICA Water Base")


class ProductContentSaveTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Маски",
            updated="2024-01-01T00:00:00Z",
        )
        self.good = GoodsModel.objects.create(
            id=501,
            title=SAMPLE_TITLE,
            description=SAMPLE_HTML,
            category=self.category,
            type="goods",
            stock=3,
            weight=90,
        )

    def test_save_keeps_weight_and_description(self):
        apply_product_content(self.good, force=True)
        self.good.refresh_from_db()
        self.assertEqual(self.good.weight, 90)
        self.assertIn("<p>Преимущества:", self.good.description)
        self.assertEqual(self.good.content_brand.slug, "23-skin-lab")
        self.assertEqual(self.good.content_kind.slug, "mask")
        ru = ProductContentBlockI18n.objects.filter(
            block__content__good=self.good,
            language="ru",
            block__kind="volume",
        ).get()
        self.assertEqual(ru.body, "50 мл")

    def test_second_apply_without_force_skips(self):
        apply_product_content(self.good, force=True)
        ProductContentBlockI18n.objects.filter(
            block__content__good=self.good,
            language="ru",
            block__kind="lead",
        ).update(body="ручная правка")
        self.assertEqual(apply_product_content(self.good, force=False), "skipped")
        lead = ProductContentBlockI18n.objects.get(
            block__content__good=self.good,
            language="ru",
            block__kind="lead",
        )
        self.assertEqual(lead.body, "ручная правка")

    def test_force_rebuilds_ru_keeps_other_language(self):
        apply_product_content(self.good, force=True)
        block = self.good.pdp_content.blocks.get(kind="lead")
        ProductContentBlockI18n.objects.create(
            block=block,
            language="en",
            body="Keep me",
        )
        self.good.description = "<p>Новый крем для лица</p><p>Объём: 30 мл</p>"
        self.good.title = "Other Brand. Soft Cream"
        self.good.save(update_fields=["description", "title"])
        apply_product_content(self.good, force=True)
        self.assertTrue(
            ProductContentBlockI18n.objects.filter(
                block__content__good=self.good,
                language="en",
                body="Keep me",
            ).exists()
        )
        volume = ProductContentBlockI18n.objects.get(
            block__content__good=self.good,
            language="ru",
            block__kind="volume",
        )
        self.assertEqual(volume.body, "30 мл")
        self.good.refresh_from_db()
        self.assertEqual(self.good.content_kind.slug, "cream")


class ParseProductContentCommandTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Маски",
            updated="2024-01-01T00:00:00Z",
        )
        for index, title in enumerate((SAMPLE_TITLE, "Sum37. Secret Cream", "Whoo. Luxury Powder"), start=601):
            GoodsModel.objects.create(
                id=index,
                title=title,
                description=f"<p>{title} — это тестовое описание</p><p>Объём: {index} мл</p><p>Вес: 10 гр</p>",
                category=self.category,
                type="goods",
                stock=1,
                weight=10,
            )

    def test_command_ids_parses_two_goods(self):
        call_command("parse_product_content", ids="601,602")
        self.assertEqual(ProductContent.objects.filter(good_id__in=[601, 602, 603]).count(), 2)
        self.assertFalse(ProductContent.objects.filter(good_id=603).exists())


class ProductContentSyncTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Кремы",
            updated="2024-01-01T00:00:00Z",
        )

    def test_sync_parses_created_only(self):
        payload = korea_payload(701, 10, SAMPLE_TITLE, total=4, weight=120)
        payload["description"] = SAMPLE_HTML
        client = FakeGoodsClient({1: [payload]})
        BusinessRuService(api_client=client).goods_to_model()
        good = GoodsModel.objects.get(id=701)
        self.assertEqual(good.weight, 120)
        self.assertTrue(ProductContent.objects.filter(good=good).exists())
        lead = ProductContentBlockI18n.objects.get(
            block__content__good=good,
            language="ru",
            block__kind="lead",
        )
        original_lead = lead.body
        payload["description"] = "<p>Другое описание крема</p>"
        payload["weight"] = 200
        payload["full_name"] = SAMPLE_TITLE
        BusinessRuService(api_client=client).goods_to_model()
        good.refresh_from_db()
        lead.refresh_from_db()
        self.assertEqual(good.weight, 200)
        self.assertEqual(good.description, "<p>Другое описание крема</p>")
        self.assertEqual(lead.body, original_lead)


class ProductContentAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "a@a.test", "pass")
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Маски",
            updated="2024-01-01T00:00:00Z",
        )
        self.good = GoodsModel.objects.create(
            id=801,
            title=SAMPLE_TITLE,
            description=SAMPLE_HTML,
            category=self.category,
            type="goods",
            stock=1,
            weight=80,
        )

    def test_parse_button_posts(self):
        self.client.force_login(self.user)
        url = reverse("admin:market_goodsmodel_parse_content", args=[self.good.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.good.refresh_from_db()
        self.assertEqual(self.good.weight, 80)
        self.assertTrue(ProductContent.objects.filter(good=self.good).exists())


class GoodsRetrieveContentApiTests(TestCase):
    def setUp(self):
        category = GroupOfGoods.objects.create(
            id=88,
            default_order="1",
            deleted=False,
            name="Маски",
            updated="2024-01-01T00:00:00Z",
        )
        self.good = GoodsModel.objects.create(
            id=2664011,
            title=SAMPLE_TITLE,
            description=SAMPLE_HTML,
            category=category,
            type="goods",
            stock=4,
            official_price=115000,
            retail_price=34000,
        )
        apply_product_content(self.good, force=True)

    def test_retrieve_keeps_legacy_fields_and_adds_blocks(self):
        response = self.client.get("/api/market/goods/2664011/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], 2664011)
        self.assertIn("<p>Преимущества:", payload["description"])
        self.assertEqual(payload["retail_price"], 34000)
        self.assertEqual(payload["content_brand"]["name"], "23 Skin Lab")
        self.assertEqual(payload["content_kind"]["slug"], "mask")
        kinds = [block["kind"] for block in payload["content_blocks"]]
        self.assertIn("lead", kinds)
        self.assertIn("benefits", kinds)
        benefits = next(block for block in payload["content_blocks"] if block["kind"] == "benefits")
        self.assertGreaterEqual(len(benefits["items"]), 2)

    def test_list_still_omits_content_blocks(self):
        response = self.client.get("/api/market/goods/")
        item = next(row for row in response.json()["results"] if row["id"] == 2664011)
        self.assertNotIn("content_blocks", item)
        self.assertEqual(item["retail_price"], 34000)
