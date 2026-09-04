from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from market.models import GoodsModel, GroupOfGoods, ImageModel


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
        )
        GoodsModel.objects.create(
            id=2,
            title="Sum37 тонер",
            description="Тонер для лица",
            category=other,
            type="goods",
            stock=0,
            bestseller=False,
            retail_price=25000,
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
