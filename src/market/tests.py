from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from market.models import GoodsModel, GroupOfGoods, ImageModel
from market.utils import BusinessRuService, parse_weight_grams


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

    def test_queue_breaks_price_ties(self):
        GoodsModel.objects.filter(id=1).update(retail_price=10000, queue=30)
        GoodsModel.objects.filter(id=2).update(retail_price=10000, queue=10)
        response = self.client.get("/api/market/goods/", {"ordering": "retail_price"})
        self.assertEqual(self._ids(response), [2, 1])
        self.assertNotIn("queue", response.json()["results"][0])

    def test_queue_breaks_title_ties(self):
        GoodsModel.objects.filter(id=1).update(title="Одинаковое", queue=20)
        GoodsModel.objects.filter(id=2).update(title="Одинаковое", queue=10)
        response = self.client.get("/api/market/goods/", {"ordering": "title"})
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
                for index in range(60)
            ]
        )

    def test_page_size_capped_at_48(self):
        response = self.client.get("/api/market/goods/", {"page_size": 1000})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 48)

    def test_catalog_page_size_12_unchanged(self):
        response = self.client.get("/api/market/goods/", {"page_size": 12})
        self.assertEqual(len(response.json()["results"]), 12)


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
