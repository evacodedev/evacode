import json
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests
from django.test import RequestFactory, SimpleTestCase

from market import views
from market.checkout_request import build_consult_text, build_telegram_order_text
from market.manager_notify import notify_managers, send_telegram

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


class CheckoutRequestTextTests(SimpleTestCase):
    def test_consult_text_has_name_and_phone(self):
        text = build_consult_text({"name": "Анна", "phone": "+77470483761"})
        self.assertIn("Имя: Анна", text)
        self.assertIn("Телефон: +77470483761", text)

    @patch("market.checkout_request.quote_shipping")
    @patch("market.checkout_request.parse_cart_lines")
    def test_order_text_uses_catalog_prices(self, parse_cart, quote):
        good = SimpleNamespace(title="Крем", retail_price=34000)
        parse_cart.return_value = (([(good, 2, 68000)], 68000), None)
        quote.return_value = ({"shipping_krw": 50000, "chargeable_weight_grams": 1000}, None)
        text = build_telegram_order_text(
            {
                "cart": [{"id": 5, "quantity": 2, "title": "Крем", "retail_price": "1 ₽"}],
                "shipping": {"method": "ems", "destination": "UZ"},
                "user": {
                    "firstName": "Анна Ким",
                    "phone": "+998901234567",
                    "email": "anna@example.com",
                    "country": "Узбекистан",
                    "city": "Ташкент",
                    "address": "ул. Навои, д. 4, кв. 4",
                    "postalCode": "100000",
                    "comment": "Позвонить",
                },
            }
        )
        self.assertIn("• Крем — 2 шт × 34 000 ₩ = 68 000 ₩", text)
        self.assertIn("Итого: 118 000 ₩", text)
        self.assertIn("Адрес: 100000, Узбекистан, Ташкент, ул. Навои, д. 4, кв. 4", text)
        self.assertIn("Email: anna@example.com", text)
        self.assertIn("Комментарий: Позвонить", text)
        self.assertNotIn("1 ₽", text)

    @patch("market.checkout_request.parse_cart_lines", return_value=(None, "Недостаточно остатка: Крем"))
    def test_order_text_survives_catalog_error(self, _parse_cart):
        text = build_telegram_order_text(
            {
                "cart": [{"id": 5, "quantity": 9, "title": "Крем"}],
                "shipping": {"method": "pickup"},
                "user": {"firstName": "Анна", "phone": "+82101234567"},
            }
        )
        self.assertIn("• Крем — 9 шт", text)
        self.assertIn("Проверка каталога: Недостаточно остатка: Крем", text)
        self.assertIn("Получение: самовывоз", text)


class CheckoutViewTests(SimpleTestCase):
    def setUp(self):
        handle, self.log_path = tempfile.mkstemp(suffix=".json")
        os.close(handle)
        os.remove(self.log_path)
        patcher = patch.object(views, "CHECKOUT_REQUESTS_FILE", self.log_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: os.path.exists(self.log_path) and os.remove(self.log_path))
        settings_patcher = patch.object(
            views.CheckoutSettings, "load", return_value=SimpleNamespace(telegram_enabled=True)
        )
        settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

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

    @patch("market.views.build_telegram_order_text", return_value="order")
    @patch("market.views.notify_managers", return_value=True)
    def test_repeat_order_is_rejected_openly(self, _notify, _text):
        body = {"consult": False, "user": {"phone": "+77470483761"}, "cart": []}
        self.assertEqual(self._post(body).status_code, 200)
        response = self._post(body)
        self.assertEqual(response.status_code, 429)
        self.assertIn("уже отправлен", json.loads(response.content)["error"])

    @patch("market.views.notify_managers", return_value=False)
    def test_failure_is_reported_and_not_remembered(self, _notify):
        body = {"consult": True, "user": {"phone": "+77470483761"}}
        response = self._post(body)
        self.assertEqual(response.status_code, 502)
        self.assertFalse(os.path.exists(self.log_path))
