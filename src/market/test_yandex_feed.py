import xml.etree.ElementTree as ET

from django.core.cache import cache
from django.test import TestCase

from core.currency_pairs import convert_krw_amount
from market.models import GoodsModel, GroupOfGoods, ImageModel, ProductBrand, ProductBrandI18n


class YandexFeedTests(TestCase):
    def setUp(self):
        cache.clear()
        parent = GroupOfGoods.objects.create(
            default_order="1",
            deleted=False,
            name="Feed уход",
            updated="2024-01-01T00:00:00Z",
        )
        child = GroupOfGoods.objects.create(
            default_order="2",
            deleted=False,
            name="Feed кремы",
            parent_id=parent,
            updated="2024-01-01T00:00:00Z",
        )
        brand = ProductBrand.objects.create(slug="feed-whoo")
        ProductBrandI18n.objects.create(brand=brand, language="ru", name="THE HISTORY OF WHOO")
        self.good = GoodsModel.objects.create(
            title="Крем <Gold>",
            description="<p>Питательный&nbsp;крем</p>",
            category=child,
            type="goods",
            stock=3,
            retail_price=120000,
            content_brand=brand,
        )
        ImageModel.objects.create(good=self.good, name="2", sort=2, url="http://a46291.business.ru/b.jpg")
        ImageModel.objects.create(good=self.good, name="1", sort=1, url="https://a46291.business.ru/a.jpg")
        self.out_of_stock = GoodsModel.objects.create(
            title="Нет остатка", category=child, type="goods", stock=0, retail_price=1000,
        )
        self.no_price = GoodsModel.objects.create(
            title="Без цены", category=child, type="goods", stock=5, retail_price=0,
        )
        self.parent_id = parent.id
        self.child_id = child.id

    def _feed(self):
        response = self.client.get("/api/market/yandex-feed/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/xml"))
        return ET.fromstring(response.content)

    def test_offer_has_rub_price_brand_pictures_and_plain_description(self):
        shop = self._feed().find("shop")
        offer_ids = [el.get("id") for el in shop.iter("offer")]
        self.assertEqual(offer_ids, [str(self.good.id)])

        offer = shop.find("offers/offer")
        self.assertEqual(offer.findtext("name"), "Крем <Gold>")
        self.assertEqual(offer.findtext("vendor"), "THE HISTORY OF WHOO")
        self.assertEqual(offer.findtext("url"), f"https://www.evacode.org/product/{self.good.id}/")
        self.assertEqual(offer.findtext("currencyId"), "RUR")
        self.assertEqual(offer.findtext("price"), str(int(convert_krw_amount(120000, "RUB"))))
        self.assertEqual(
            [el.text for el in offer.findall("picture")],
            ["https://a46291.business.ru/a.jpg", "https://a46291.business.ru/b.jpg"],
        )
        self.assertEqual(offer.findtext("description"), "Питательный крем")

    def test_categories_include_parent_chain(self):
        shop = self._feed().find("shop")
        categories = {el.get("id"): el for el in shop.findall("categories/category")}
        self.assertEqual(set(categories), {str(self.parent_id), str(self.child_id)})
        self.assertEqual(categories[str(self.child_id)].get("parentId"), str(self.parent_id))
        self.assertIsNone(categories[str(self.parent_id)].get("parentId"))
