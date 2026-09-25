from django.test import TestCase

from market.models import GoodsModel, GroupOfGoods, ProductBrand


class CatalogSitemapApiTests(TestCase):
    def setUp(self):
        category = GroupOfGoods.objects.create(
            default_order="1",
            deleted=False,
            name="Sitemap кремы",
            updated="2024-01-01T00:00:00Z",
        )
        in_stock = GoodsModel.objects.create(
            title="В наличии",
            category=category,
            type="goods",
            stock=4,
            retail_price=1000,
        )
        out_stock = GoodsModel.objects.create(
            title="Нет остатка",
            category=category,
            type="goods",
            stock=0,
            retail_price=1000,
        )
        ProductBrand.objects.create(slug="sitemap-jogabi", page_published=True)
        ProductBrand.objects.create(slug="sitemap-hidden", page_published=False)
        self.in_stock_id = in_stock.id
        self.out_stock_id = out_stock.id

    def test_includes_catalog_products_and_published_brands(self):
        response = self.client.get("/api/market/sitemap/")
        self.assertEqual(response.status_code, 200)
        locs = [item["loc"] for item in response.json()["urls"]]
        self.assertEqual(locs[0], "/collection/leftsidebar/0/")
        self.assertIn("/brand/sitemap-jogabi/", locs)
        self.assertNotIn("/brand/sitemap-hidden/", locs)
        self.assertIn(f"/product/{self.in_stock_id}/", locs)
        self.assertNotIn(f"/product/{self.out_stock_id}/", locs)
