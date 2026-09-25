from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from market.models import (
    GoodsModel,
    GroupOfGoods,
    ImageModel,
    PartnerApiKey,
    ProductBrand,
    ProductBrandI18n,
    ProductKind,
    ProductKindI18n,
)
from market.utils import (
    BusinessRuBarcodeLookup,
    BusinessRuGoodPricesLookup,
    BusinessRuService,
    parse_weight_grams,
    serialize_krw_prices,
)


class GoodsFilterApiTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Кремы",
            updated="2024-01-01T00:00:00Z",
        )
        other = GroupOfGoods.objects.create(
            id=11,
            default_order="2",
            deleted=False,
            name="Сыворотки",
            updated="2024-01-01T00:00:00Z",
        )
        GoodsModel.objects.create(
            id=1,
            title="Whoo крем",
            description="Увлажняющий крем",
            category=self.category,
            type="goods",
            stock=5,
            bestseller=True,
            retail_price=10000,
            weight=150,
        )
        GoodsModel.objects.create(
            id=2,
            title="Sum37 тонер",
            description="Тонер для лица",
            category=other,
            type="goods",
            stock=3,
            bestseller=False,
            retail_price=25000,
        )
        GoodsModel.objects.create(
            id=3,
            title="Скрытый",
            description="Нет остатка",
            category=other,
            type="goods",
            stock=0,
            bestseller=False,
            retail_price=1000,
        )

    def _ids(self, response):
        return [item["id"] for item in response.json()["results"]]

    def test_filter_by_category(self):
        response = self.client.get("/api/market/goods/", {"category": 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._ids(response), [1])

    def test_filter_bestseller(self):
        response = self.client.get("/api/market/goods/", {"bestseller": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._ids(response), [1])
        payload = response.json()["results"][0]
        self.assertTrue(payload["bestseller"])
        self.assertIn("content_brand", payload)
        self.assertIn("content_kind", payload)

    def test_search_by_title(self):
        response = self.client.get("/api/market/goods/", {"search": "whoo"})
        self.assertEqual(self._ids(response), [1])

    def test_price_range(self):
        response = self.client.get("/api/market/goods/", {"min_price": 20000, "max_price": 30000})
        self.assertEqual(self._ids(response), [2])

    def test_ordering_by_price(self):
        response = self.client.get("/api/market/goods/", {"ordering": "retail_price"})
        self.assertEqual(self._ids(response), [1, 2])

    def test_default_ordering_by_title(self):
        response = self.client.get("/api/market/goods/")
        self.assertEqual(self._ids(response), [2, 1])

    def test_queue_comes_before_title(self):
        GoodsModel.objects.filter(id=1).update(queue=10)
        response = self.client.get("/api/market/goods/", {"ordering": "title"})
        self.assertEqual(self._ids(response), [1, 2])
        self.assertNotIn("queue", response.json()["results"][0])

    def test_queue_comes_before_price(self):
        GoodsModel.objects.filter(id=2).update(queue=10)
        response = self.client.get("/api/market/goods/", {"ordering": "retail_price"})
        self.assertEqual(self._ids(response), [2, 1])

    def test_list_includes_weight_grams(self):
        response = self.client.get("/api/market/goods/")
        by_id = {item["id"]: item for item in response.json()["results"]}
        self.assertEqual(by_id[1]["weight"], 150)
        self.assertIsNone(by_id[2]["weight"])
        self.assertNotIn(3, by_id)

    def test_zero_stock_is_hidden(self):
        response = self.client.get("/api/market/goods/")
        self.assertEqual(self._ids(response), [2, 1])
        missing = self.client.get("/api/market/goods/3/")
        self.assertEqual(missing.status_code, 404)


class CatalogContentFilterApiTests(TestCase):
    def setUp(self):
        category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Кремы",
            updated="2024-01-01T00:00:00Z",
        )
        whoo = ProductBrand.objects.create(slug="the-history-of-whoo")
        ProductBrandI18n.objects.create(brand=whoo, language="ru", name="THE HISTORY OF WHOO")
        o_hui = ProductBrand.objects.create(slug="o-hui")
        ProductBrandI18n.objects.create(brand=o_hui, language="ru", name="O HUI")
        ProductBrand.objects.create(slug="empty-brand")
        cream = ProductKind.objects.create(slug="cream")
        ProductKindI18n.objects.create(kind=cream, language="ru", name="крем")
        toner = ProductKind.objects.create(slug="toner")
        ProductKindI18n.objects.create(kind=toner, language="ru", name="тонер")
        GoodsModel.objects.create(
            id=1,
            title="Whoo крем",
            description="Увлажняющий крем",
            category=category,
            type="goods",
            stock=5,
            retail_price=10000,
            content_brand=whoo,
            content_kind=cream,
        )
        GoodsModel.objects.create(
            id=2,
            title="O HUI тонер",
            description="Тонер для лица",
            category=category,
            type="goods",
            stock=3,
            retail_price=25000,
            content_brand=o_hui,
            content_kind=toner,
        )
        GoodsModel.objects.create(
            id=3,
            title="Whoo скрытый",
            description="Нет остатка",
            category=category,
            type="goods",
            stock=0,
            retail_price=1000,
            content_brand=whoo,
            content_kind=cream,
        )

    def _ids(self, response):
        return [item["id"] for item in response.json()["results"]]

    def test_filter_by_brand(self):
        response = self.client.get("/api/market/goods/", {"brand": "the-history-of-whoo"})
        self.assertEqual(self._ids(response), [1])

    def test_filter_by_several_brands(self):
        response = self.client.get("/api/market/goods/", {"brand": "the-history-of-whoo,o-hui"})
        self.assertEqual(self._ids(response), [2, 1])

    def test_filter_by_kind(self):
        response = self.client.get("/api/market/goods/", {"kind": "cream"})
        self.assertEqual(self._ids(response), [1])

    def test_filter_brand_and_kind(self):
        response = self.client.get(
            "/api/market/goods/",
            {"brand": "the-history-of-whoo", "kind": "cream"},
        )
        self.assertEqual(self._ids(response), [1])
        empty = self.client.get("/api/market/goods/", {"brand": "o-hui", "kind": "cream"})
        self.assertEqual(self._ids(empty), [])

    def test_empty_brand_does_not_filter(self):
        response = self.client.get("/api/market/goods/", {"brand": ""})
        self.assertEqual(self._ids(response), [2, 1])

    def test_catalog_facets_skip_empty_and_out_of_stock(self):
        response = self.client.get("/api/market/catalog-filters/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        brands = {item["slug"]: item for item in payload["brands"]}
        kinds = {item["slug"]: item for item in payload["kinds"]}
        self.assertEqual(brands["o-hui"]["name"], "O HUI")
        self.assertEqual(brands["o-hui"]["count"], 1)
        self.assertEqual(brands["the-history-of-whoo"]["count"], 1)
        self.assertNotIn("empty-brand", brands)
        self.assertEqual(kinds["cream"]["name"], "крем")
        self.assertEqual(kinds["cream"]["count"], 1)
        self.assertEqual([item["slug"] for item in payload["kinds"]], ["toner", "cream"])
        self.assertEqual(
            [item["slug"] for item in payload["brands"]],
            ["o-hui", "the-history-of-whoo"],
        )


class HomePageApiTests(TestCase):
    def setUp(self):
        category, _ = GroupOfGoods.objects.update_or_create(
            id=20,
            defaults={
                "default_order": "1",
                "deleted": False,
                "name": "Уход",
                "updated": "2024-01-01T00:00:00Z",
            },
        )
        GoodsModel.objects.filter(id__in=(101, 102, 103)).delete()
        curacion, _ = ProductBrand.objects.update_or_create(
            slug="curacion",
            defaults={"page_published": True},
        )
        ProductBrandI18n.objects.update_or_create(
            brand=curacion,
            language="ru",
            defaults={"name": "Curación", "lead": "Лакто-уход"},
        )
        ProductBrand.objects.update_or_create(
            slug="jogabi",
            defaults={"page_published": True},
        )
        ProductBrand.objects.update_or_create(
            slug="tom-tit-tot",
            defaults={"page_published": False},
        )
        cream, _ = ProductKind.objects.update_or_create(slug="cream")
        ProductKindI18n.objects.update_or_create(
            kind=cream, language="ru", defaults={"name": "крем"}
        )
        eye, _ = ProductKind.objects.update_or_create(slug="eye_cream")
        ProductKindI18n.objects.update_or_create(
            kind=eye, language="ru", defaults={"name": "крем для глаз"}
        )
        ProductKind.objects.update_or_create(slug="set")
        GoodsModel.objects.create(
            id=101,
            title="Hit cream",
            description="hit",
            category=category,
            type="goods",
            stock=5,
            bestseller=True,
            retail_price=10000,
            content_brand=curacion,
            content_kind=cream,
        )
        GoodsModel.objects.create(
            id=102,
            title="Eye cream",
            description="eye",
            category=category,
            type="goods",
            stock=4,
            bestseller=False,
            retail_price=12000,
            content_brand=curacion,
            content_kind=eye,
        )
        GoodsModel.objects.create(
            id=103,
            title="Another cream",
            description="similar",
            category=category,
            type="goods",
            stock=3,
            bestseller=False,
            retail_price=9000,
            content_brand=curacion,
            content_kind=cream,
        )

    def test_home_bundle_shape(self):
        response = self.client.get("/api/market/home/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["id"] for item in payload["bestsellers"]], [101])
        self.assertIn(103, [item["id"] for item in payload["recommend"]])
        self.assertNotIn(101, [item["id"] for item in payload["recommend"]])
        self.assertEqual(payload["kinds"]["cream"]["chosen"]["slug"], "cream")
        self.assertEqual(
            [item["id"] for item in payload["kinds"]["cream"]["results"]],
            [103, 101],
        )
        self.assertEqual(payload["brands"]["curacion"]["brand"]["name"], "Curación")
        self.assertEqual(
            [item["id"] for item in payload["brands"]["curacion"]["results"]],
            [103, 102, 101],
        )
        self.assertIsNone(payload["brands"]["tom-tit-tot"]["brand"])
        self.assertEqual(payload["brands"]["tom-tit-tot"]["results"], [])


class ParseWeightGramsTests(TestCase):
    def test_parse_weight_grams(self):
        self.assertEqual(parse_weight_grams("150"), 150)
        self.assertEqual(parse_weight_grams(150.4), 150)
        self.assertEqual(parse_weight_grams(150.6), 151)
        self.assertIsNone(parse_weight_grams(None))
        self.assertIsNone(parse_weight_grams(""))
        self.assertIsNone(parse_weight_grams("abc"))


class GoodsListPrefetchTests(TestCase):
    def setUp(self):
        category = GroupOfGoods.objects.create(
            id=30,
            default_order="1",
            deleted=False,
            name="Тест",
            updated="2024-01-01T00:00:00Z",
        )
        for index in range(3):
            good = GoodsModel.objects.create(
                id=100 + index,
                title=f"Товар {index}",
                description="текст",
                category=category,
                type="goods",
                stock=1,
                bestseller=False,
                retail_price=1000 + index,
            )
            ImageModel.objects.create(
                good=good,
                name=f"one-{index}",
                url=f"https://cdn.example/{index}-a.jpg",
                sort=1,
            )
            ImageModel.objects.create(
                good=good,
                name=f"two-{index}",
                url=f"https://cdn.example/{index}-b.jpg",
                sort=2,
            )

    def test_list_loads_images_in_one_query(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/market/goods/", {"page_size": 12})
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 3)
        self.assertEqual(len(results[0]["images"]), 1)
        self.assertEqual(results[0]["excerpt"], "текст")
        self.assertNotIn("description", results[0])
        self.assertNotIn("wholesale_price", results[0])
        self.assertNotIn("large_wholesale_price", results[0])
        image_queries = [
            query["sql"]
            for query in ctx.captured_queries
            if "market_imagemodel" in query["sql"].lower()
        ]
        self.assertEqual(len(image_queries), 1)

    def test_retrieve_keeps_full_payload(self):
        response = self.client.get("/api/market/goods/100/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["description"], "текст")
        self.assertIn("wholesale_price", payload)
        self.assertEqual(len(payload["images"]), 2)
        self.assertIn("content_blocks", payload)
        self.assertEqual(payload["content_blocks"], [])
        self.assertIsNone(payload["content_brand"])
        self.assertIsNone(payload["content_kind"])

    def test_list_omits_pdp_content_fields(self):
        response = self.client.get("/api/market/goods/", {"page_size": 12})
        item = response.json()["results"][0]
        self.assertNotIn("content_blocks", item)
        self.assertNotIn("content_brand", item)
        self.assertNotIn("content_kind", item)


class GoodsPageSizeCapTests(TestCase):
    def setUp(self):
        category = GroupOfGoods.objects.create(
            id=40,
            default_order="1",
            deleted=False,
            name="Лимит",
            updated="2024-01-01T00:00:00Z",
        )
        GoodsModel.objects.bulk_create(
            [
                GoodsModel(
                    id=200 + index,
                    title=f"Товар {index:03d}",
                    description="",
                    category=category,
                    type="goods",
                    stock=1,
                    bestseller=False,
                    retail_price=1000,
                )
                for index in range(110)
            ]
        )

    def test_page_size_capped_at_100(self):
        response = self.client.get("/api/market/goods/", {"page_size": 1000})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 100)

    def test_catalog_page_size_12_unchanged(self):
        response = self.client.get("/api/market/goods/", {"page_size": 12})
        self.assertEqual(len(response.json()["results"]), 12)

    def test_catalog_page_size_100(self):
        response = self.client.get("/api/market/goods/", {"page_size": 100})
        self.assertEqual(len(response.json()["results"]), 100)


class CategorySiteOrderApiTests(TestCase):
    def test_categories_sorted_by_site_order(self):
        GroupOfGoods.objects.create(
            id=21,
            default_order="1",
            site_order=20,
            deleted=False,
            name="Вторая",
            updated="2024-01-01T00:00:00Z",
        )
        GroupOfGoods.objects.create(
            id=20,
            default_order="9",
            site_order=10,
            deleted=False,
            name="Первая",
            updated="2024-01-01T00:00:00Z",
        )
        GroupOfGoods.objects.create(
            id=22,
            default_order="0",
            site_order=None,
            deleted=False,
            name="Без порядка",
            updated="2024-01-01T00:00:00Z",
        )
        response = self.client.get("/api/market/categories/")
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.json()["result"]]
        self.assertEqual(names, ["Первая", "Вторая", "Без порядка"])


class FakeGoodsClient:
    def __init__(self, pages, fail_on_page=None):
        self.pages = pages
        self.fail_on_page = fail_on_page

    def get_goods(self, page=1, **kwargs):
        if self.fail_on_page is not None and page == self.fail_on_page:
            raise RuntimeError("Business.Ru timeout")
        return self.pages.get(page, [])


def korea_payload(good_id, group_id, title, total, reserved=0, weight=100, images=None):
    return {
        "id": str(good_id),
        "group_id": str(group_id),
        "full_name": title,
        "description": title,
        "type": "goods",
        "weight": weight,
        "attributes": [],
        "prices": [{"price_type": {"name": "Розничная Цена"}, "price": 5000}],
        "remains": [
            {
                "store": {"name": "Корея"},
                "amount": {"total": total, "reserved": reserved},
            }
        ],
        "images": images or [],
    }


class GoodsSyncTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Кремы",
            updated="2024-01-01T00:00:00Z",
        )

    def test_creates_updates_and_hides_without_delete(self):
        stale = GoodsModel.objects.create(
            id=3,
            title="Старый",
            category=self.category,
            type="goods",
            stock=8,
        )
        existing = GoodsModel.objects.create(
            id=1,
            title="Был",
            category=self.category,
            type="goods",
            stock=1,
        )
        ImageModel.objects.create(good=existing, name="old", url="https://cdn.example/old.jpg", sort=1)
        client = FakeGoodsClient(
            {
                1: [
                    korea_payload(
                        1,
                        10,
                        "Новый",
                        total=5,
                        images=[{"name": "new", "url": "https://cdn.example/new.jpg", "sort": 1}],
                    ),
                    korea_payload(2, 10, "Без Кореи", total=4, images=[]),
                ]
            }
        )
        client.pages[1][1]["remains"] = [
            {"store": {"name": "Москва"}, "amount": {"total": 4, "reserved": 0}}
        ]
        BusinessRuService(api_client=client).goods_to_model()

        created = GoodsModel.objects.get(id=1)
        self.assertEqual(created.title, "Новый")
        self.assertEqual(created.stock, 5)
        self.assertEqual(created.weight, 100)
        self.assertEqual(list(created.images.values_list("url", flat=True)), ["https://cdn.example/new.jpg"])
        self.assertFalse(GoodsModel.objects.filter(id=2).exists())
        stale.refresh_from_db()
        self.assertEqual(stale.stock, 0)
        self.assertTrue(GoodsModel.objects.filter(id=3).exists())

        client.pages[1][0]["full_name"] = "Обновлённый"
        client.pages[1][0]["remains"][0]["amount"]["total"] = 9
        BusinessRuService(api_client=client).goods_to_model()
        created.refresh_from_db()
        self.assertEqual(created.title, "Обновлённый")
        self.assertEqual(created.stock, 9)

    def test_incomplete_sync_does_not_hide_unseen(self):
        kept = GoodsModel.objects.create(
            id=4,
            title="Не трогать",
            category=self.category,
            type="goods",
            stock=7,
        )
        client = FakeGoodsClient(
            {1: [korea_payload(1, 10, "Первая страница", total=2)]},
            fail_on_page=2,
        )
        with self.assertRaises(RuntimeError):
            BusinessRuService(api_client=client).goods_to_model()
        kept.refresh_from_db()
        self.assertEqual(kept.stock, 7)
        self.assertEqual(GoodsModel.objects.get(id=1).stock, 2)


class FakeBarcodeClient:
    def __init__(self, handlers):
        self.handlers = handlers
        self.calls = []

    def get_json(self, model, extra=None):
        extra = extra or {}
        self.calls.append((model, extra))
        handler = self.handlers.get(model)
        if handler is None:
            return {"result": []}
        if callable(handler):
            return handler(extra)
        return handler


class BarcodeLookupTests(TestCase):
    def test_finds_via_barcodes_model(self):
        payload = korea_payload(12, 10, "Sum37", total=2)

        def goods(extra):
            if str(extra.get("id")) == "12":
                return {"result": [payload]}
            return {"result": []}

        client = FakeBarcodeClient(
            {
                "goods": goods,
                "barcodes": {"result": [{"value": "490123", "good_id": "12"}]},
            }
        )
        found = BusinessRuBarcodeLookup(api_client=client).find("490123")
        self.assertEqual(int(found["id"]), 12)
        self.assertEqual(found["barcode"], "490123")
        self.assertEqual(client.calls[0], ("barcodes", {"value": "490123"}))

    def test_find_all_returns_every_matching_good(self):
        first = korea_payload(12, 10, "Набор", total=1)
        second = korea_payload(13, 10, "Набор промо", total=1)

        def goods(extra):
            good_id = str(extra.get("id") or "")
            if good_id == "12":
                return {"result": [first]}
            if good_id == "13":
                return {"result": [second]}
            return {"result": []}

        client = FakeBarcodeClient(
            {
                "goods": goods,
                "barcodes": {
                    "result": [
                        {"value": "880111", "good_id": "12"},
                        {"value": "880111", "good_id": "13"},
                    ]
                },
            }
        )
        found = BusinessRuBarcodeLookup(api_client=client).find_all("880111")
        self.assertEqual([int(item["id"]) for item in found], [12, 13])

    def test_skips_archived_goods(self):
        live = korea_payload(12, 10, "Живой", total=1)
        live["archive"] = 0
        archived = korea_payload(13, 10, "Архив", total=1)
        archived["archive"] = 1
        also_archived = korea_payload(14, 10, "Тоже архив", total=1)
        also_archived["archive"] = 1

        def goods(extra):
            mapping = {"12": live, "13": archived, "14": also_archived}
            payload = mapping.get(str(extra.get("id") or ""))
            return {"result": [payload] if payload else []}

        client = FakeBarcodeClient(
            {
                "goods": goods,
                "barcodes": {
                    "result": [
                        {"value": "8809816980900", "good_id": "12"},
                        {"value": "8809816980900", "good_id": "13"},
                        {"value": "8809816980900", "good_id": "14"},
                    ]
                },
            }
        )
        found = BusinessRuBarcodeLookup(api_client=client).find_all("8809816980900")
        self.assertEqual([int(item["id"]) for item in found], [12])

    def test_ignores_unrelated_barcode_rows(self):
        client = FakeBarcodeClient(
            {
                "barcodes": {"result": [{"value": "880111", "good_id": "11"}]},
                "goodssearch": {"result": {"goods": {}}},
            }
        )
        self.assertIsNone(BusinessRuBarcodeLookup(api_client=client).find("12312351gsdfvwerg"))

    def test_finds_via_goodssearch_when_barcode_found(self):
        payload = korea_payload(15, 10, "Sulwhasoo", total=1)

        def goods(extra):
            if str(extra.get("id")) == "15":
                return {"result": [payload]}
            return {"result": []}

        client = FakeBarcodeClient(
            {
                "goods": goods,
                "barcodes": {"result": []},
                "goodssearch": {
                    "result": {
                        "goods": {
                            "a0": {"good_id": "15", "barcode_found": True, "name": "Sulwhasoo"},
                        }
                    }
                },
            }
        )
        found = BusinessRuBarcodeLookup(api_client=client).find("8809925186569")
        self.assertEqual(int(found["id"]), 15)

    def test_unknown_barcodes_model_is_skipped(self):
        client = FakeBarcodeClient(
            {
                "goods": {"result": []},
                "barcodes": lambda extra: (_ for _ in ()).throw(ValueError("Модель barcodes не найдена")),
                "goodssearch": {"result": {"goods": {}}},
            }
        )
        self.assertIsNone(BusinessRuBarcodeLookup(api_client=client).find("111"))


class GoodsByBarcodeApiTests(TestCase):
    def setUp(self):
        self.key = PartnerApiKey.objects.create(name="Тест", token="test-partner-token")
        self.auth = {"HTTP_X_API_KEY": self.key.token}

    def test_requires_token(self):
        response = self.client.get("/api/market/goods/by-barcode/", {"barcode": "000"})
        self.assertEqual(response.status_code, 401)

    def test_rejects_invalid_token(self):
        response = self.client.get(
            "/api/market/goods/by-barcode/",
            {"barcode": "000"},
            HTTP_X_API_KEY="wrong",
        )
        self.assertEqual(response.status_code, 401)

    def test_rejects_inactive_token(self):
        self.key.is_active = False
        self.key.save(update_fields=["is_active"])
        response = self.client.get("/api/market/goods/by-barcode/", {"barcode": "000"}, **self.auth)
        self.assertEqual(response.status_code, 401)

    def test_accepts_bearer_token(self):
        with patch("market.views.BusinessRuBarcodeLookup") as lookup_cls:
            lookup_cls.return_value.find_all.return_value = []
            response = self.client.get(
                "/api/market/goods/by-barcode/",
                {"barcode": "000"},
                HTTP_AUTHORIZATION=f"Bearer {self.key.token}",
            )
        self.assertEqual(response.status_code, 404)

    def test_catalog_stays_public(self):
        response = self.client.get("/api/market/goods/")
        self.assertEqual(response.status_code, 200)

    def test_requires_barcode(self):
        response = self.client.get("/api/market/goods/by-barcode/", **self.auth)
        self.assertEqual(response.status_code, 400)

    def test_not_found(self):
        with patch("market.views.BusinessRuBarcodeLookup") as lookup_cls:
            lookup_cls.return_value.find_all.return_value = []
            response = self.client.get("/api/market/goods/by-barcode/", {"barcode": "000"}, **self.auth)
        self.assertEqual(response.status_code, 404)

    def test_returns_business_ru_fields(self):
        payload = korea_payload(11, 10, "Whoo крем", total=4, weight=150)
        payload["barcode"] = "8801234567890"
        payload["part"] = "WHOO-01"
        with patch("market.views.BusinessRuBarcodeLookup") as lookup_cls:
            lookup_cls.return_value.find_all.return_value = [payload]
            response = self.client.get("/api/market/goods/by-barcode/", {"barcode": "8801234567890"}, **self.auth)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["results"]), 1)
        item = data["results"][0]
        self.assertEqual(item["id"], 11)
        self.assertEqual(item["title"], "Whoo крем")
        self.assertEqual(item["part"], "WHOO-01")
        self.assertEqual(item["barcode"], "8801234567890")
        self.assertEqual(item["weight"], 150)
        self.assertNotIn("retail_price", item)
        self.assertNotIn("stock", item)

    def test_returns_count_for_several_goods(self):
        first = korea_payload(11, 10, "Набор", total=1)
        first["barcode"] = "880111"
        second = korea_payload(12, 10, "Набор промо", total=1)
        second["barcode"] = "880111"
        with patch("market.views.BusinessRuBarcodeLookup") as lookup_cls:
            lookup_cls.return_value.find_all.return_value = [first, second]
            response = self.client.get("/api/market/goods/by-barcode/", {"barcode": "880111"}, **self.auth)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual([item["id"] for item in data["results"]], [11, 12])

    def test_business_ru_error(self):
        with patch("market.views.BusinessRuBarcodeLookup") as lookup_cls:
            lookup_cls.return_value.find_all.side_effect = ValueError("timeout")
            response = self.client.get("/api/market/goods/by-barcode/", {"barcode": "880"}, **self.auth)
        self.assertEqual(response.status_code, 502)


class AdminAppListTests(TestCase):
    def test_ems_and_settings_are_separate_groups(self):
        User.objects.create_superuser("admin", "admin@example.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertRegex(html, r">EMS</")
        self.assertRegex(html, r">SETTINGS</")
        self.assertRegex(html, r">Оплаты</")
        self.assertIn("Токены API партнёров", html)
        self.assertIn("Направления EMS", html)
        self.assertIn("Заказы с сайта", html)
        self.assertIn("Оплата на сайте", html)
        payments_pos = html.find(">Оплаты</")
        orders_pos = html.find("Заказы с сайта")
        self.assertGreater(payments_pos, 0)
        self.assertGreater(orders_pos, payments_pos)


def _krw_price(name, amount, symbol="₩"):
    return {
        "price": amount,
        "price_type": {"name": name, "currency": {"symbol": symbol, "code": "KRW" if symbol == "₩" else ""}},
    }


class KrwPricesTests(TestCase):
    def test_serialize_keeps_only_won_types(self):
        payload = serialize_krw_prices(
            {
                "id": "943196",
                "prices": [
                    _krw_price("Крупный опт", "38000"),
                    _krw_price("Средний опт", "42000"),
                    _krw_price("Мелкий опт", "48000"),
                    _krw_price("Розничная Цена", "61000"),
                    {
                        "price": "82500",
                        "price_type": {"name": "С. Каз Офиц цена", "currency": {"symbol": "₸", "code": "KZT"}},
                    },
                    _krw_price("Официальная Цена", "220000"),
                    {
                        "price": "12338",
                        "price_type": {"name": "KZ закупка", "currency": {"symbol": "₸", "code": "KZT"}},
                    },
                    _krw_price("Закупочная Цена", "28260"),
                    {
                        "price": "1681",
                        "price_type": {"name": "Рос закуп", "currency": {"symbol": "₽", "code": "RUB"}},
                    },
                ],
            }
        )
        self.assertEqual(
            payload,
            {
                "id": 943196,
                "purchase_price": 28260,
                "official_price": 220000,
                "recommended_price": None,
                "retail_price": 61000,
                "small_wholesale_price": 48000,
                "medium_wholesale_price": 42000,
                "large_wholesale_price": 38000,
            },
        )

    def test_lookup_returns_archived_by_id(self):
        client = FakeBarcodeClient(
            {
                "goods": {
                    "result": [
                        {
                            "id": "11",
                            "archive": 1,
                            "prices": [_krw_price("Розничная Цена", "1000")],
                        }
                    ]
                }
            }
        )
        payload = BusinessRuGoodPricesLookup(api_client=client).get(11)
        self.assertEqual(payload["id"], 11)
        self.assertEqual(payload["retail_price"], 1000)

    def test_lookup_fills_purchase_from_currentprices(self):
        client = FakeBarcodeClient(
            {
                "goods": {
                    "result": [
                        {
                            "id": "11",
                            "prices": [_krw_price("Розничная Цена", "61000")],
                        }
                    ]
                },
                "buypricetypes": {
                    "result": [
                        {"id": "75622", "name": "Закупочная Цена", "currency": "14"},
                        {"id": "936485", "name": "KZ закупка", "currency": "7"},
                    ]
                },
                "currentprices": {
                    "result": [
                        {"good_id": "11", "price_type_id": "75622", "price": "28260"},
                        {"good_id": "11", "price_type_id": "936485", "price": "12338"},
                    ]
                },
            }
        )
        payload = BusinessRuGoodPricesLookup(api_client=client).get(11)
        self.assertEqual(payload["purchase_price"], 28260)
        self.assertEqual(payload["retail_price"], 61000)

    def test_lookup_requires_matching_id(self):
        client = FakeBarcodeClient(
            {
                "goods": {
                    "result": [
                        {
                            "id": "99",
                            "prices": [_krw_price("Розничная Цена", "1000")],
                        }
                    ]
                }
            }
        )
        self.assertIsNone(BusinessRuGoodPricesLookup(api_client=client).get(11))


class GoodsKrwPricesApiTests(TestCase):
    def setUp(self):
        self.key = PartnerApiKey.objects.create(name="Тест", token="test-partner-token")
        self.auth = {"HTTP_X_API_KEY": self.key.token}

    def test_requires_token(self):
        response = self.client.get("/api/market/goods/11/prices/")
        self.assertEqual(response.status_code, 401)

    def test_catalog_detail_stays_public(self):
        category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Кремы",
            updated="2024-01-01T00:00:00Z",
        )
        GoodsModel.objects.create(
            id=11,
            title="Whoo",
            category=category,
            type="goods",
            stock=2,
            retail_price=61000,
        )
        response = self.client.get("/api/market/goods/11/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("purchase_price", response.json())

    def test_returns_krw_prices(self):
        with patch("market.views.BusinessRuGoodPricesLookup") as lookup_cls:
            lookup_cls.return_value.get.return_value = {
                "id": 11,
                "purchase_price": 28260,
                "official_price": 220000,
                "recommended_price": None,
                "retail_price": 61000,
                "small_wholesale_price": 48000,
                "medium_wholesale_price": 42000,
                "large_wholesale_price": 38000,
            }
            response = self.client.get("/api/market/goods/11/prices/", **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["purchase_price"], 28260)
        self.assertIsNone(response.json()["recommended_price"])

    def test_not_found(self):
        with patch("market.views.BusinessRuGoodPricesLookup") as lookup_cls:
            lookup_cls.return_value.get.return_value = None
            response = self.client.get("/api/market/goods/11/prices/", **self.auth)
        self.assertEqual(response.status_code, 404)
