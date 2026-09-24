import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from core.models import CurrencyPair, Contacts
from market.models import CheckoutSettings, GoodsModel, GroupOfGoods, SiteOrder, SiteOrderItem


@override_settings(
    PAYPAL_CLIENT_ID="test-id",
    PAYPAL_SECRET="test-secret",
    PAYPAL_MODE="sandbox",
    BACKEND_PUBLIC_URL="https://backend.test/",
    FRONTEND_PUBLIC_URL="https://front.test/",
)
class SiteOrderApiTests(TestCase):
    def setUp(self):
        CurrencyPair.objects.update_or_create(
            base="KRW",
            quote="USD",
            defaults={
                "name": "Доллар США",
                "symbol": "$",
                "rate": Decimal("0.0008831169"),
                "sort": 20,
                "is_active": True,
            },
        )
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
            weight=400,
        )
        CheckoutSettings.objects.update_or_create(
            pk=1,
            defaults={"paypal_enabled": True, "telegram_enabled": False},
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
            "shipping": {"method": "pickup", "destination": "KR"},
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
        self.assertEqual(len(str(order.public_id)), 8)
        self.assertEqual(order.amount_krw, 20000)
        self.assertEqual(order.shipping_krw, 0)
        self.assertEqual(order.shipping_method, "pickup")
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

    def test_create_order_pickup_without_address(self):
        payload = self._payload()
        payload["user"]["country"] = ""
        payload["user"]["city"] = ""
        payload["user"]["address"] = ""
        with patch("market.order_views.create_order") as create_order_mock, patch(
            "market.order_views.krw_to_usd", return_value=(Decimal("12.50"), Decimal("1600"))
        ):
            create_order_mock.return_value = ({"id": "PAYPAL-3"}, "https://paypal.test/approve")
            response = self.client.post(
                "/api/market/orders/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200, response.content)
        order = SiteOrder.objects.get(public_id=response.json()["id"])
        self.assertEqual(order.country, "Корея")
        self.assertEqual(order.address, "Самовывоз")

    def test_shipping_quote_ems_adds_postage(self):
        from io import BytesIO

        from market.ems_tariffs import import_ems_xlsx
        from market.test_ems_tariffs import make_ems_xlsx

        import_ems_xlsx(BytesIO(make_ems_xlsx()))
        response = self.client.post(
            "/api/market/shipping/quote/",
            data=json.dumps({
                "cart": [{"id": self.good.id, "quantity": 2}],
                "shipping": {"method": "ems", "destination": "RU"},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["shipping_krw"], 57000)
        self.assertEqual(data["weight_grams"], 800)
        self.assertEqual(data["packing_grams"], 500)
        self.assertEqual(data["chargeable_weight_grams"], 1300)

    @patch("market.order_views.create_order")
    @patch("market.order_views.krw_to_usd", return_value=(Decimal("48.13"), Decimal("1600")))
    def test_create_order_includes_ems_in_total(self, _rate, create_order_mock):
        from io import BytesIO

        from market.ems_tariffs import import_ems_xlsx
        from market.test_ems_tariffs import make_ems_xlsx

        import_ems_xlsx(BytesIO(make_ems_xlsx()))
        create_order_mock.return_value = ({"id": "PAYPAL-4"}, "https://paypal.test/approve")
        payload = self._payload(shipping={"method": "ems", "destination": "RU"})
        payload["user"]["country"] = "Россия"
        response = self.client.post(
            "/api/market/orders/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        order = SiteOrder.objects.get(public_id=response.json()["id"])
        self.assertEqual(order.goods_krw, 20000)
        self.assertEqual(order.shipping_krw, 57000)
        self.assertEqual(order.amount_krw, 77000)
        self.assertEqual(order.postal_code, "12345")
        self.assertEqual(order.weight_grams, 1300)
        self.assertEqual(create_order_mock.call_args.kwargs["amount_usd"], Decimal("48.13"))

    def test_create_order_ems_requires_postal_code(self):
        from io import BytesIO

        from market.ems_tariffs import import_ems_xlsx
        from market.test_ems_tariffs import make_ems_xlsx

        import_ems_xlsx(BytesIO(make_ems_xlsx()))
        payload = self._payload(shipping={"method": "ems", "destination": "RU"})
        payload["user"]["country"] = "Россия"
        payload["user"]["postalCode"] = ""
        response = self.client.post(
            "/api/market/orders/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("postalCode", response.json().get("errors", {}))

    def test_destinations_skip_korea(self):
        response = self.client.get("/api/market/shipping/destinations/")
        self.assertEqual(response.status_code, 200)
        codes = [item["code"] for item in response.json()["results"]]
        self.assertNotIn("KR", codes)

    def test_shipping_quote_weight_without_country(self):
        response = self.client.post(
            "/api/market/shipping/quote/",
            data=json.dumps({
                "cart": [{"id": self.good.id, "quantity": 2}],
                "shipping": {"method": "ems", "destination": ""},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["weight_grams"], 800)
        self.assertEqual(data["packing_grams"], 500)
        self.assertEqual(data["chargeable_weight_grams"], 1300)
        self.assertIsNone(data["shipping_krw"])

    def test_checkout_settings_are_public(self):
        CheckoutSettings.objects.update_or_create(
            pk=1,
            defaults={"paypal_enabled": False, "telegram_enabled": True},
        )
        response = self.client.get("/api/market/checkout-settings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"paypal_enabled": False, "telegram_enabled": True, "paypal_sandbox": False},
        )

    def test_create_order_forbidden_when_paypal_disabled(self):
        CheckoutSettings.objects.update_or_create(
            pk=1,
            defaults={"paypal_enabled": False, "telegram_enabled": False},
        )
        response = self.client.post(
            "/api/market/orders/",
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SiteOrder.objects.exists())

    def _login(self, email, *, staff=False):
        from django.contrib.auth.models import User

        User.objects.create_user(email, email, "StrongPass123", is_staff=staff, is_superuser=staff)
        login = self.client.post(
            "/api/core/auth/login/",
            data={"email": email, "password": "StrongPass123"},
            content_type="application/json",
        )
        self.assertEqual(login.status_code, 200, login.content)
        return login.json()["access"]

    @override_settings(
        PAYPAL_MODE="live",
        PAYPAL_CLIENT_ID="live-id",
        PAYPAL_SECRET="live-secret",
        PAYPAL_SANDBOX_CLIENT_ID="sb-id",
        PAYPAL_SANDBOX_SECRET="sb-secret",
        PAYPAL_SANDBOX_EMAILS="vadim.k@evacode.co.kr",
    )
    @patch("market.order_views.create_order")
    @patch("market.order_views.krw_to_usd", return_value=(Decimal("12.50"), Decimal("1600")))
    def test_staff_tester_uses_paypal_sandbox(self, _rate, create_order_mock):
        create_order_mock.return_value = ({"id": "PAYPAL-SB"}, "https://sandbox.paypal.test/approve")
        token = self._login("vadim.k@evacode.co.kr", staff=True)

        settings_response = self.client.get(
            "/api/market/checkout-settings/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(settings_response.status_code, 200)
        self.assertTrue(settings_response.json()["paypal_sandbox"])

        response = self.client.post(
            "/api/market/orders/",
            data=json.dumps(self._payload()),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(create_order_mock.call_args.kwargs["mode"], "sandbox")
        order = SiteOrder.objects.get(public_id=response.json()["id"])
        self.assertEqual(order.paypal_mode, "sandbox")

    @override_settings(
        PAYPAL_MODE="live",
        PAYPAL_CLIENT_ID="live-id",
        PAYPAL_SECRET="live-secret",
        PAYPAL_SANDBOX_CLIENT_ID="sb-id",
        PAYPAL_SANDBOX_SECRET="sb-secret",
        PAYPAL_SANDBOX_EMAILS="vadim.k@evacode.co.kr",
    )
    @patch("market.order_views.create_order")
    @patch("market.order_views.krw_to_usd", return_value=(Decimal("12.50"), Decimal("1600")))
    def test_guest_and_plain_user_use_paypal_live(self, _rate, create_order_mock):
        create_order_mock.return_value = ({"id": "PAYPAL-LIVE"}, "https://paypal.test/approve")

        guest = self.client.post(
            "/api/market/orders/",
            data=json.dumps(self._payload(user={
                **self._payload()["user"],
                "email": "vadim.k@evacode.co.kr",
            })),
            content_type="application/json",
        )
        self.assertEqual(guest.status_code, 200, guest.content)
        self.assertEqual(create_order_mock.call_args.kwargs["mode"], "live")
        self.assertEqual(SiteOrder.objects.get(public_id=guest.json()["id"]).paypal_mode, "live")

        token = self._login("buyer@example.com", staff=False)
        buyer = self.client.post(
            "/api/market/orders/",
            data=json.dumps(self._payload()),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(buyer.status_code, 200, buyer.content)
        self.assertEqual(create_order_mock.call_args.kwargs["mode"], "live")

        settings_response = self.client.get(
            "/api/market/checkout-settings/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertFalse(settings_response.json()["paypal_sandbox"])

    @override_settings(PAYPAL_MODE="live")
    @patch("market.order_views.capture_order")
    @patch("market.order_views._complete_paid_order", return_value=True)
    def test_paypal_return_captures_in_stored_sandbox_mode(self, _complete, capture_mock):
        capture_mock.return_value = {"status": "COMPLETED"}
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
            paypal_order_id="PAYPAL-SB-RETURN",
            paypal_mode="sandbox",
        )
        response = self.client.get("/api/market/orders/paypal/return/", {"token": "PAYPAL-SB-RETURN"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(capture_mock.call_args.kwargs["mode"], "sandbox")
        self.assertIn(str(order.public_id), response["Location"])

    @patch("django.db.close_old_connections")
    @patch("market.order_views._notify_telegram")
    @patch("market.order_views.send_order_confirmation_email")
    @patch("market.order_views.export_paid_order")
    def test_sandbox_paid_order_exports_business_ru(self, export_mock, email_mock, notify_mock, _close):
        from market.order_views import _export_paid_side_effects

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
            paypal_mode="sandbox",
            status=SiteOrder.Status.PAID,
        )

        def _fake_export(saved):
            saved.business_ru_order_id = "BR-1"
            saved.business_ru_order_number = "ЗП-1"
            saved.business_ru_payment_id = "PAY-1"
            saved.business_ru_reservation_id = "RES-1"
            saved.save(
                update_fields=[
                    "business_ru_order_id",
                    "business_ru_order_number",
                    "business_ru_payment_id",
                    "business_ru_reservation_id",
                ]
            )

        export_mock.side_effect = _fake_export
        _export_paid_side_effects(order.pk)
        export_mock.assert_called_once()
        email_mock.assert_called_once()
        notify_mock.assert_called_once()

    def test_logged_in_order_links_user_and_lists_in_cabinet(self):
        token = self._login("buyer@example.com", staff=False)
        with patch("market.order_views.create_order") as create_order_mock, patch(
            "market.order_views.krw_to_usd", return_value=(Decimal("12.50"), Decimal("1600"))
        ):
            create_order_mock.return_value = ({"id": "PAYPAL-USER"}, "https://paypal.test/approve")
            response = self.client.post(
                "/api/market/orders/",
                data=json.dumps(self._payload()),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
        self.assertEqual(response.status_code, 200, response.content)
        order = SiteOrder.objects.get(public_id=response.json()["id"])
        self.assertEqual(order.user.email, "buyer@example.com")
        order.status = SiteOrder.Status.PAID
        order.save(update_fields=["status"])

        orphan = SiteOrder.objects.create(
            first_name="Buyer",
            phone="+821011122233",
            phone_digits="821011122233",
            email="buyer@example.com",
            country="KR",
            city="Seoul",
            address="Street",
            amount_krw=5000,
            amount_usd=Decimal("3.00"),
            status=SiteOrder.Status.PAID,
        )
        mine = self.client.get(
            "/api/market/orders/mine/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(mine.status_code, 200, mine.content)
        ids = [item["id"] for item in mine.json()["results"]]
        self.assertIn(str(order.public_id), ids)
        self.assertIn(str(orphan.public_id), ids)
        orphan.refresh_from_db()
        self.assertEqual(orphan.user_id, order.user_id)

    @patch("market.order_views.async_to_sync")
    def test_order_help_sends_telegram(self, async_to_sync_mock):
        from unittest.mock import MagicMock

        token = self._login("buyer@example.com", staff=False)
        order = SiteOrder.objects.create(
            first_name="Buyer",
            phone="+821011122233",
            phone_digits="821011122233",
            email="buyer@example.com",
            country="KR",
            city="Seoul",
            address="Street",
            amount_krw=10000,
            amount_usd=Decimal("6.25"),
            status=SiteOrder.Status.PAID,
            business_ru_order_number="ЗП-265650",
        )
        send_mock = MagicMock()
        async_to_sync_mock.return_value = send_mock
        with patch("market.views.bot", MagicMock()), patch("market.views.chat_id", "123"), patch(
            "market.views.keyboard", None
        ):
            response = self.client.post(
                f"/api/market/orders/{order.public_id}/help/",
                data=json.dumps({"phone": "+821011122233", "message": "Где мой заказ?"}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json().get("ok"))
        send_mock.assert_called_once()
        text = send_mock.call_args.kwargs.get("text") or ""
        self.assertIn("ПОМОЩЬ С ЗАКАЗОМ", text)
        self.assertIn("ЗП-265650", text)


@override_settings(
    EMAIL_HOST_USER="orders@evacode.co.kr",
    DEFAULT_FROM_EMAIL="Evacode <orders@evacode.co.kr>",
)
class OrderConfirmationEmailTests(TestCase):
    def setUp(self):
        Contacts.objects.create(
            telegram="https://t.me/test",
            instagram="https://instagram.com/test",
            facebook="https://facebook.com/test",
            address=(
                "경기 안산시 단원구 별망로 555 4 этаж №420"
                "<br>"
                "Gyeonggi-do, Ansan-si, Danwon-gu, Byeolmang-ro 555, 4th Floor, No. 420"
            ),
            phone="+821000000000",
            email="orders@evacode.co.kr",
            tiktok="",
        )
        self.order = SiteOrder.objects.create(
            status=SiteOrder.Status.PAID,
            first_name="Ivan",
            phone="+821011122233",
            phone_digits="821011122233",
            email="ivan@example.com",
            country="Korea",
            city="Seoul",
            address="",
            postal_code="",
            shipping_method="pickup",
            amount_krw=20000,
            amount_usd=Decimal("12.50"),
            goods_krw=20000,
            business_ru_order_id="2825388",
            business_ru_order_number="ЗП-100",
        )
        SiteOrderItem.objects.create(
            order=self.order,
            good_id_snapshot=101,
            title="Тестовый крем",
            quantity=2,
            price_krw=10000,
            line_total_krw=20000,
        )

    def test_sends_pickup_confirmation_once(self):
        from django.core import mail

        from market.order_email import send_order_confirmation_email

        self.assertTrue(send_order_confirmation_email(self.order))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("ЗП-100", message.subject)
        self.assertIn("ЗП-100", message.body)
        self.assertIn("Самовывоз", message.body)
        self.assertIn("별망로 555", message.body)
        self.assertIn("Тестовый крем", message.body)
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.confirmation_email_sent_at)
        self.assertFalse(send_order_confirmation_email(self.order))
        self.assertEqual(len(mail.outbox), 1)
