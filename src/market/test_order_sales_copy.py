from decimal import Decimal

from django.test import TestCase

from market.models import SiteOrder, SiteOrderItem
from market.order_sales_copy import format_sales_inquiry


class SalesInquiryCopyTests(TestCase):
    def test_format_includes_contacts_items_and_totals(self):
        order = SiteOrder.objects.create(
            first_name="Гульшат Шайнурова",
            phone="79870405573",
            phone_digits="79870405573",
            email="shainurova00@bk.ru",
            country="Россия",
            city="Уфа",
            address="Степана Халтурина, д. 28",
            postal_code="450009",
            shipping_method="ems",
            shipping_destination="RU",
            shipping_krw=39500,
            goods_krw=34000,
            weight_grams=780,
            amount_krw=73500,
            amount_usd=Decimal("67.00"),
            comment="Позвонить после 18:00",
        )
        SiteOrderItem.objects.create(
            order=order,
            good_id_snapshot=1,
            title="Тестовый крем",
            quantity=2,
            price_krw=17000,
            line_total_krw=34000,
        )
        text = format_sales_inquiry(order)
        self.assertIn("Обращение с сайта Evacode", text)
        self.assertIn(order.public_id, text)
        self.assertIn("Гульшат Шайнурова", text)
        self.assertIn("79870405573", text)
        self.assertIn("shainurova00@bk.ru", text)
        self.assertIn("Доставка EMS RU: 39500 ₩, 780 г", text)
        self.assertIn("Тестовый крем — 2 шт — 17000 ₩", text)
        self.assertIn("Итого: 73500 ₩ / 67.00 USD", text)
        self.assertIn("Позвонить после 18:00", text)

    def test_pickup_shipping_line(self):
        order = SiteOrder.objects.create(
            first_name="Иван",
            phone="+821011122233",
            phone_digits="821011122233",
            email="ivan@example.com",
            country="Корея",
            city="Самовывоз",
            address="Самовывоз",
            shipping_method="pickup",
            amount_krw=10000,
            amount_usd=Decimal("9.00"),
            goods_krw=10000,
        )
        text = format_sales_inquiry(order)
        self.assertIn("Доставка: самовывоз", text)
