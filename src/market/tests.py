from django.test import TestCase

from market.models import GoodsModel, GroupOfGoods


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
