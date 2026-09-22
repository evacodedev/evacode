from django.test import TestCase

from market.brand_pages import ensure_jogabi_brand
from market.models import GoodsModel, GroupOfGoods, ProductBrand, ProductBrandI18n


class BrandPageApiTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=40,
            default_order="1",
            deleted=False,
            name="Уход",
            updated="2024-01-01T00:00:00Z",
        )
        self.hidden = ProductBrand.objects.create(slug="ohui")
        ProductBrandI18n.objects.create(brand=self.hidden, language="ru", name="O HUI")
        self.good = GoodsModel.objects.create(
            id=401,
            title="JOGABI The Origin 1943 Cream",
            description="Крем",
            category=self.category,
            type="goods",
            stock=3,
            official_price=85000,
            retail_price=85000,
        )

    def test_unpublished_brand_is_404(self):
        response = self.client.get("/api/market/brands/ohui/")
        self.assertEqual(response.status_code, 404)

    def test_missing_brand_is_404(self):
        response = self.client.get("/api/market/brands/unknown/")
        self.assertEqual(response.status_code, 404)

    def test_jogabi_page_and_goods_link(self):
        brand = ensure_jogabi_brand()
        self.good.refresh_from_db()
        self.assertEqual(self.good.content_brand_id, brand.id)
        response = self.client.get("/api/market/brands/jogabi/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["name"], "JOGABI")
        self.assertEqual(payload["native_caption"], "이화조개비")
        self.assertIn("ракуш", payload["history"])
        self.assertNotIn("раковин", payload["history"].casefold())
        self.assertEqual(payload["history_title"], "Имя из ракушки")
        self.assertTrue(payload["partnership"])
        self.assertEqual(len(payload["gallery"]), 3)
        self.assertEqual(payload["video_url"], "https://www.youtube.com/watch?v=kT6It0g0jgA")
        self.assertEqual(payload["facts"], [
            {"value": "1943", "label": "История бренда начинается в Сеуле."},
        ])
        self.assertEqual(payload["lines"][0]["title"], "The Originals")
        goods = self.client.get("/api/market/goods/", {"brand": "jogabi"})
        self.assertEqual(goods.status_code, 200)
        self.assertEqual(goods.json()["results"][0]["id"], 401)
        detail = self.client.get("/api/market/goods/401/")
        self.assertEqual(detail.json()["content_brand"]["page"], True)
        hidden = self.client.get("/api/market/goods/", {"brand": "ohui"})
        self.assertEqual(hidden.json()["count"], 0)
