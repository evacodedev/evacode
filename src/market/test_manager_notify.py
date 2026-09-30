import json
import os
import tempfile
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from market import order_views, views
from market.checkout_request import build_consult_text, build_manager_order_text
from market.manager_notify import notify_managers, send_telegram
from market.models import SiteOrder

TELEGRAM_ENV = {"BOT_TOKEN": "123:abc", "CHAT_ID": "-100500"}


def _ok_response():
    response = MagicMock(ok=True, status_code=200)
    response.json.return_value = {"ok": True}
    return response


@patch.dict(os.environ, TELEGRAM_ENV)
@patch("market.manager_notify.time.sleep")
class SendTelegramTests(SimpleTestCase):
    @patch("market.manager_notify.requests.post")
    def test_retries_after_timeout(self, post, _sleep):
        post.side_effect = [requests.ConnectTimeout("hang"), _ok_response()]
        self.assertTrue(send_telegram("Заказ"))
        self.assertEqual(post.call_count, 2)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["chat_id"], "-100500")
        self.assertEqual(payload["text"], "Заказ")

    @patch("market.manager_notify.requests.post")
    def test_gives_up_after_three_attempts(self, post, _sleep):
        post.side_effect = requests.ConnectTimeout("hang")
        self.assertFalse(send_telegram("Заказ"))
        self.assertEqual(post.call_count, 3)

    @patch("market.manager_notify.requests.post")
    def test_bad_request_is_not_retried(self, post, _sleep):
        post.return_value = MagicMock(ok=False, status_code=400, text="chat not found")
        self.assertFalse(send_telegram("Заказ"))
        self.assertEqual(post.call_count, 1)


class NotifyManagersTests(SimpleTestCase):
    @patch("market.manager_notify.send_managers_email")
    @patch("market.manager_notify.send_telegram", return_value=True)
    def test_email_not_sent_when_telegram_works(self, _telegram, email):
        self.assertTrue(notify_managers("text", subject="s"))
        email.assert_not_called()

    @patch("market.manager_notify.send_managers_email", return_value=True)
    @patch("market.manager_notify.send_telegram", return_value=False)
    def test_falls_back_to_email(self, _telegram, email):
        self.assertTrue(notify_managers("text", subject="s", reply_to="client@example.com"))
        subject, body, reply_to = email.call_args.args
        self.assertEqual(subject, "s")
        self.assertIn("text", body)
        self.assertEqual(reply_to, "client@example.com")


class PaidOrderNotifyTests(SimpleTestCase):
    @staticmethod
    def _order(**overrides):
        item = SimpleNamespace(title="Крем", quantity=1, price_krw=34000)
        fields = {
            "public_id": "DPHG544E",
            "paypal_mode": "live",
            "amount_krw": 85000,
            "amount_usd": Decimal("61.00"),
            "first_name": "Vadim Kim",
            "phone": "+821022795599",
            "email": "client@example.com",
            "postal_code": "15434",
            "country": "Узбекистан",
            "city": "Ansan",
            "address": "улица, д. 3",
            "shipping_method": "ems",
            "shipping_destination": "UZ",
            "shipping_krw": 51000,
            "weight_grams": 1520,
            "comment": "",
            "business_ru_order_id": "2877820",
            "business_ru_error": "",
            "items": SimpleNamespace(all=lambda: [item]),
        }
        fields.update(overrides)
        return SimpleNamespace(**fields)

    @patch("market.manager_notify.send_telegram")
    @patch("market.order_views.send_managers_email", return_value=True)
    def test_paid_order_goes_to_email_not_telegram(self, email, telegram):
        order_views._notify_paid_order(self._order())
        telegram.assert_not_called()
        subject, body = email.call_args.args
        self.assertEqual(subject, "ОПЛАЧЕННЫЙ ЗАКАЗ С САЙТА DPHG544E")
        self.assertIn("Крем — 1 шт — 34000 ₩", body)
        self.assertIn("Business.Ru заказ: 2877820", body)
        self.assertEqual(email.call_args.kwargs["reply_to"], "client@example.com")

    @patch("market.manager_notify.send_telegram")
    @patch("market.order_views.send_managers_email", return_value=True)
    def test_sandbox_subject_is_marked(self, email, telegram):
        order_views._notify_paid_order(self._order(paypal_mode="sandbox"))
        telegram.assert_not_called()
        self.assertEqual(email.call_args.args[0], "ТЕСТ PAYPAL SANDBOX DPHG544E")


class CheckoutRequestTextTests(SimpleTestCase):
    def test_consult_text_has_name_and_phone(self):
        text = build_consult_text({"name": "Анна", "phone": "+77470483761"})
        self.assertIn("Имя: Анна", text)
        self.assertIn("Телефон: +77470483761", text)

    @staticmethod
    def _order(**overrides):
        fields = {
            "public_id": "A1B2C3",
            "goods_krw": 68000,
            "shipping_method": "ems",
            "shipping_krw": 50000,
            "weight_grams": 1200,
            "amount_krw": 118000,
            "amount_usd": Decimal("85.10"),
            "first_name": "Анна Ким",
            "phone": "+998901234567",
            "email": "anna@example.com",
            "postal_code": "100000",
            "country": "Узбекистан",
            "city": "Ташкент",
            "address": "ул. Навои, д. 4, кв. 4",
            "comment": "Позвонить",
        }
        fields.update(overrides)
        return SimpleNamespace(**fields)

    def test_order_text_has_number_items_and_address(self):
        item = SimpleNamespace(title="Крем", quantity=2, price_krw=34000, line_total_krw=68000)
        text = build_manager_order_text(self._order(), [item])
        self.assertIn("№ A1B2C3", text)
        self.assertIn("не оплачен", text)
        self.assertIn("• Крем — 2 шт × 34 000 ₩ = 68 000 ₩", text)
        self.assertIn("Доставка EMS: 50 000 ₩, 1200 г", text)
        self.assertIn("Итого: 118 000 ₩ (≈ 85.10 USD)", text)
        self.assertIn("Адрес: 100000, Узбекистан, Ташкент, ул. Навои, д. 4, кв. 4", text)
        self.assertIn("Комментарий: Позвонить", text)

    def test_pickup_order_without_usd(self):
        order = self._order(shipping_method="pickup", shipping_krw=0, amount_usd=Decimal("0"), comment="")
        text = build_manager_order_text(order, [])
        self.assertIn("Доставка: самовывоз", text)
        self.assertIn("Получение: самовывоз", text)
        self.assertNotIn("USD", text)
        self.assertNotIn("Комментарий", text)


class CheckoutViewTests(SimpleTestCase):
    def setUp(self):
        handle, self.log_path = tempfile.mkstemp(suffix=".json")
        os.close(handle)
        os.remove(self.log_path)
        patcher = patch.object(views, "CHECKOUT_REQUESTS_FILE", self.log_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: os.path.exists(self.log_path) and os.remove(self.log_path))

    def _post(self, body):
        request = RequestFactory().post(
            "/api/market/checkout/", data=json.dumps(body), content_type="application/json"
        )
        return views.Checkout.as_view()(request)

    @patch("market.views.notify_managers", return_value=True)
    def test_consult_is_sent_once_per_window(self, notify):
        body = {"consult": True, "user": {"phone": "+77470483761", "name": "Анна"}}
        self.assertEqual(self._post(body).status_code, 200)
        self.assertEqual(self._post(body).status_code, 200)
        self.assertEqual(notify.call_count, 1)

    @patch("market.views.notify_managers", return_value=True)
    def test_unsaved_order_is_not_sent(self, notify):
        body = {"consult": False, "user": {"phone": "+77470483761"}, "cart": []}
        self.assertEqual(self._post(body).status_code, 410)
        notify.assert_not_called()

    @patch("market.views.notify_managers", return_value=False)
    def test_failure_is_reported_and_not_remembered(self, _notify):
        body = {"consult": True, "user": {"phone": "+77470483761"}}
        response = self._post(body)
        self.assertEqual(response.status_code, 502)
        self.assertFalse(os.path.exists(self.log_path))


class TelegramOrderViewTests(SimpleTestCase):
    FORM = {"first_name": "Анна", "phone": "+7 747 048-37-61", "email": "anna@example.com"}
    QUOTE = {"method": "pickup", "destination": "", "shipping_krw": 0, "weight_grams": 0}

    def setUp(self):
        self.patches = {
            "settings": patch.object(
                order_views.CheckoutSettings, "load", return_value=SimpleNamespace(telegram_enabled=True)
            ),
            "validate": patch.object(
                order_views, "_validate_order_request", return_value=(self.FORM, [], 68000, self.QUOTE, {})
            ),
            "filter": patch.object(SiteOrder.objects, "filter"),
            "usd": patch.object(order_views, "krw_to_usd", return_value=(Decimal("48.00"), Decimal("0.0007"))),
            "create": patch.object(
                order_views, "_create_order_record", return_value=SimpleNamespace(pk=7, public_id="A1B2C3")
            ),
            "thread": patch.object(order_views.threading, "Thread"),
        }
        self.mocks = {name: p.start() for name, p in self.patches.items()}
        for p in self.patches.values():
            self.addCleanup(p.stop)
        self.mocks["filter"].return_value.exists.return_value = False

    def _post(self):
        request = RequestFactory().post("/api/market/orders/telegram/", data={}, content_type="application/json")
        request.user = AnonymousUser()
        return order_views.CreateTelegramOrderView.as_view()(request)

    def test_order_is_saved_as_manager_and_sent_in_background(self):
        response = self._post()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content), {"id": "A1B2C3"})
        kwargs = self.mocks["create"].call_args.kwargs
        self.assertEqual(kwargs["status"], SiteOrder.Status.MANAGER)
        self.assertNotIn("paypal_mode", kwargs)
        thread_kwargs = self.mocks["thread"].call_args.kwargs
        self.assertIs(thread_kwargs["target"], order_views._notify_manager_order)
        self.assertEqual(thread_kwargs["args"], (7,))
        self.mocks["thread"].return_value.start.assert_called_once()
        self.assertEqual(self.mocks["filter"].call_args.kwargs["phone_digits"], "77470483761")

    def test_repeat_from_same_phone_is_rejected(self):
        self.mocks["filter"].return_value.exists.return_value = True
        response = self._post()
        self.assertEqual(response.status_code, 429)
        self.mocks["create"].assert_not_called()

    def test_disabled_in_admin(self):
        self.mocks["settings"].return_value = SimpleNamespace(telegram_enabled=False)
        self.assertEqual(self._post().status_code, 403)
        self.mocks["create"].assert_not_called()

    def test_saved_even_without_usd_rate(self):
        self.mocks["usd"].side_effect = RuntimeError("rate down")
        self.assertEqual(self._post().status_code, 201)
        self.assertEqual(self.mocks["create"].call_args.kwargs["amount_usd"], Decimal("0"))

    def test_form_errors_are_returned(self):
        self.mocks["validate"].return_value = (self.FORM, None, 0, None, {"email": "Укажите корректный email"})
        response = self._post()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)["errors"]["email"], "Укажите корректный email")
