import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.models import Currency
from market.models import GoodsModel, GroupOfGoods, SiteOrder


@override_settings(
    PAYPAL_CLIENT_ID="test-id",
    PAYPAL_SECRET="test-secret",
    PAYPAL_MODE="sandbox",
    BACKEND_PUBLIC_URL="https://backend.test/",
    FRONTEND_PUBLIC_URL="https://front.test/",
)
class SiteOrderApiTests(TestCase):
    def setUp(self):
        Currency.objects.create(name="eur", key="krw-rub-eur", value=Decimal("13"))
        category = GroupOfGoods.objects.create(
            id=20,
            default_order="1",
            deleted=False,
            name="Тест",
            updated="2024-01-01T00:00:00Z",
        )
        self.good = GoodsModel.objects.create(
            id=101,
            title="Тестовый крем",
            description="",
            category=category,
            type="goods",
            stock=5,
            retail_price=10000,
        )

    def _payload(self, **overrides):
        body = {
            "user": {
                "firstName": "Ivan Petrov",
                "phone": "+821011122233",
                "email": "ivan@example.com",
                "country": "Korea",
                "city": "Seoul",
                "address": "Test street 1",
                "postalCode": "12345",
                "comment": "",
            },
            "cart": [{"id": self.good.id, "quantity": 2}],
        }
        body.update(overrides)
        return body

    @patch("market.order_views.create_order")
    @patch("market.order_views.krw_to_usd", return_value=(Decimal("12.50"), Decimal("1600")))
    def test_create_order_uses_server_price_and_paypal_url(self, _rate, create_order_mock):
        create_order_mock.return_value = ({"id": "PAYPAL-1", "links": []}, "https://paypal.test/approve")

        response = self.client.post(
            "/api/market/orders/",
            data=json.dumps(self._payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["approve_url"], "https://paypal.test/approve")
        order = SiteOrder.objects.get(public_id=data["id"])
        self.assertEqual(order.amount_krw, 20000)
        self.assertEqual(order.amount_usd, Decimal("12.50"))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.paypal_order_id, "PAYPAL-1")
        self.assertEqual(order.status, SiteOrder.Status.PENDING)

    def test_create_order_rejects_short_name(self):
        payload = self._payload()
        payload["user"]["firstName"] = "A"
        response = self.client.post(
            "/api/market/orders/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("market.order_views._complete_paid_order", return_value=True)
    @patch("market.order_views.capture_order")
    def test_paypal_return_redirects_to_success(self, capture_mock, _complete):
        order = SiteOrder.objects.create(
            first_name="Ivan",
            phone="+821011122233",
            phone_digits="821011122233",
            email="ivan@example.com",
            country="KR",
            city="Seoul",
            address="Street",
            amount_krw=10000,
            amount_usd=Decimal("6.25"),
            paypal_order_id="PAYPAL-2",
        )
        capture_mock.return_value = {"status": "COMPLETED"}

        response = self.client.get("/api/market/orders/paypal/return/", {"token": "PAYPAL-2"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(order.public_id), response["Location"])
        self.assertIn("order-success", response["Location"])
