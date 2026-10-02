from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from market.models import SiteOrder
from market.order_email import (
    STAGE_ACCEPTED,
    STAGE_PAID,
    STAGE_SHIPPED,
    OrderEmailError,
    build_client_email,
    send_order_accepted_email,
    send_order_tracking_email,
)

CONTACTS = {
    "phone": "+8210-7652-8595",
    "email": "orders@evacode.co.kr",
    "instagram": "https://www.instagram.com/evacodeorg",
    "tiktok": "https://www.tiktok.com/@evacodeorg",
    "facebook": "",
    "address": "경기 안산시 단원구 별망로 555, 4층 №420",
}
_contacts_patch = patch("market.order_email._shop_contacts", return_value=CONTACTS)


def setUpModule():
    _contacts_patch.start()


def tearDownModule():
    _contacts_patch.stop()


def _order(**overrides):
    item = SimpleNamespace(title="Крем <Лёгкий>", quantity=2, price_krw=17000, line_total_krw=34000, good=None)
    fields = {
        "pk": 5,
        "Status": SiteOrder.Status,
        "status": SiteOrder.Status.PAID,
        "public_id": "DPHG544E",
        "business_ru_order_number": "ЗП-265700",
        "business_ru_order_id": "2877820",
        "first_name": "Vadim Kim",
        "phone": "+821022795599",
        "email": "client@example.com",
        "postal_code": "15434",
        "country": "Uzbekistan",
        "city": "Tashkent",
        "address": "Navoi St 4, Apt. 4",
        "shipping_method": "ems",
        "shipping_destination": "UZ",
        "shipping_krw": 51000,
        "goods_krw": 34000,
        "amount_krw": 85000,
        "amount_usd": Decimal("61.00"),
        "paid_at": None,
        "accepted_email_sent_at": None,
        "tracking_number": "",
        "tracking_email_sent_at": None,
        "items": SimpleNamespace(all=lambda: [item]),
        "save": MagicMock(),
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


@override_settings(FRONTEND_PUBLIC_URL="https://evacode.co.kr")
class ClientEmailBodyTests(SimpleTestCase):
    def test_paid_email_marks_payment_and_waiting(self):
        subject, text, html = build_client_email(_order(), STAGE_PAID)
        self.assertEqual(subject, "Evacode — заказ ЗП-265700 оплачен")
        self.assertIn("ждёт подтверждения", text)
        self.assertIn("Оплата прошла", html)
        self.assertIn("Крем &lt;Лёгкий&gt;", html)
        self.assertIn("Navoi St 4, Apt. 4", html)
        self.assertIn("https://evacode.co.kr/account", html)

    def test_contacts_block(self):
        _subject, text, html = build_client_email(_order(), STAGE_ACCEPTED)
        self.assertIn("Связаться с нами", html)
        self.assertIn('href="tel:+821076528595"', html)
        self.assertIn("https://wa.me/77470483761", html)
        self.assertIn("https://wa.me/77776122046", html)
        self.assertIn("https://t.me/+77776868917", html)
        self.assertNotIn("t.me/+77470483761", html)
        self.assertIn("max.ru/u/", html)
        self.assertIn("https://www.tiktok.com/@evacodeorg", html)
        self.assertNotIn("Facebook", html)
        self.assertIn("별망로 555", html)
        self.assertIn("WhatsApp: +7 747 048 3761, +7 777 612 2046", text)
        self.assertNotIn("Telegram: +7 747 048 3761", text)
        self.assertIn("Instagram: https://www.instagram.com/evacodeorg", text)

    def test_accepted_email_promises_tracking(self):
        subject, text, _html = build_client_email(_order(), STAGE_ACCEPTED)
        self.assertEqual(subject, "Evacode — заказ ЗП-265700 принят в обработку")
        self.assertIn("пришлём письмо с трек-номером", text)
        self.assertIn("Доставим EMS по адресу:", text)
        self.assertIn("Итого: 85 000 ₩", text)

    def test_shipped_email_has_tracking_link(self):
        subject, text, html = build_client_email(_order(), STAGE_SHIPPED, tracking_number="EG123456789KR")
        self.assertIn("EG123456789KR", subject)
        self.assertIn("https://t.17track.net/ru#nums=EG123456789KR", text)
        self.assertIn("Отследить посылку", html)
        self.assertNotIn("пока заказ не отправлен", html)

    @patch("market.order_email._pickup_address", return_value="Ansan, Byeolmang-ro 555")
    def test_pickup_accepted_email(self, _pickup):
        order = _order(shipping_method="pickup", shipping_krw=0, amount_krw=34000)
        _subject, text, html = build_client_email(order, STAGE_ACCEPTED)
        self.assertIn("готов к выдаче", text)
        self.assertIn("Byeolmang-ro 555", html)
        self.assertIn("Можно забрать", html)

    def test_catalog_image_goes_through_imgproxy_as_jpeg(self):
        image = SimpleNamespace(url="http://a46291.business.ru/cdn/public/1/abc")
        images = MagicMock()
        images.order_by.return_value.first.return_value = image
        item = SimpleNamespace(title="Тонер", quantity=1, price_krw=1000, line_total_krw=1000, good=SimpleNamespace(images=images))
        _subject, _text, html = build_client_email(_order(items=SimpleNamespace(all=lambda: [item])), STAGE_PAID)
        self.assertIn("https://evacode.co.kr/img/insecure/rs:fit:128:128/q:80/f:jpg/", html)


@override_settings(EMAIL_HOST_USER="orders@evacode.co.kr")
@patch("market.order_email._send_to_client")
class ClientEmailSendTests(SimpleTestCase):
    def test_accepted_sets_timestamp(self, send):
        order = _order()
        send_order_accepted_email(order)
        self.assertIn("принят в обработку", send.call_args.args[1])
        self.assertIsNotNone(order.accepted_email_sent_at)
        order.save.assert_called_once()

    def test_unpaid_order_is_rejected(self, send):
        with self.assertRaises(OrderEmailError):
            send_order_accepted_email(_order(status=SiteOrder.Status.MANAGER))
        send.assert_not_called()

    def test_tracking_is_normalized_and_saved(self, send):
        order = _order()
        self.assertEqual(send_order_tracking_email(order, " eg 1234 5678 9kr "), "EG123456789KR")
        self.assertEqual(order.tracking_number, "EG123456789KR")
        self.assertIsNotNone(order.tracking_email_sent_at)

    def test_bad_tracking_is_rejected(self, send):
        for value in ("", "ЕГ123456789", "EG1"):
            with self.subTest(value=value), self.assertRaises(OrderEmailError):
                send_order_tracking_email(_order(), value)
        send.assert_not_called()

    def test_pickup_needs_no_tracking(self, send):
        with self.assertRaises(OrderEmailError):
            send_order_tracking_email(_order(shipping_method="pickup"), "EG123456789KR")
        send.assert_not_called()


@override_settings(EMAIL_HOST_USER="orders@evacode.co.kr")
@patch("market.order_email._send_to_client")
class StatusEmailTestRecipientTests(SimpleTestCase):
    @override_settings(ORDER_STATUS_EMAIL_TEST_TO="vadim.k@evacode.co.kr")
    def test_accepted_and_tracking_go_to_test_address(self, send):
        self.assertEqual(send_order_accepted_email(_order()), "vadim.k@evacode.co.kr")
        send_order_tracking_email(_order(), "EG123456789KR")
        for call in send.call_args_list:
            self.assertEqual(call.kwargs["to"], "vadim.k@evacode.co.kr")
            self.assertTrue(call.args[1].startswith("[ТЕСТ, клиент: client@example.com] "))

    @override_settings(ORDER_STATUS_EMAIL_TEST_TO="")
    def test_without_test_address_goes_to_client(self, send):
        self.assertEqual(send_order_accepted_email(_order()), "client@example.com")
        self.assertEqual(send.call_args.kwargs["to"], "client@example.com")
        self.assertFalse(send.call_args.args[1].startswith("[ТЕСТ"))

    @override_settings(ORDER_STATUS_EMAIL_TEST_TO="vadim.k@evacode.co.kr", FRONTEND_PUBLIC_URL="https://evacode.co.kr")
    def test_paid_email_still_goes_to_client(self, send):
        from market.order_email import send_order_confirmation_email

        self.assertTrue(send_order_confirmation_email(_order(confirmation_email_sent_at=None)))
        self.assertEqual(send.call_args.kwargs.get("to", ""), "")
        self.assertEqual(send.call_args.args[1], "Evacode — заказ ЗП-265700 оплачен")


class ClientMailAdminPageTests(SimpleTestCase):
    def test_template_and_urls(self):
        from django.template.loader import get_template
        from django.urls import reverse

        get_template("admin/market/siteorder/change_form.html")
        self.assertEqual(
            reverse("admin:market_siteorder_confirm_received", args=[7]),
            "/admin/market/siteorder/7/confirm-received/",
        )
        self.assertEqual(
            reverse("admin:market_siteorder_send_tracking", args=[7]),
            "/admin/market/siteorder/7/send-tracking/",
        )


class ConfirmReceivedActionTests(SimpleTestCase):
    def _admin(self):
        from django.contrib import admin

        from market.admin import SiteOrderAdmin

        model_admin = SiteOrderAdmin(SiteOrder, admin.site)
        model_admin.message_user = MagicMock()
        return model_admin

    @patch("market.admin.send_order_accepted_email")
    def test_skips_already_confirmed(self, send):
        from django.utils import timezone

        model_admin = self._admin()
        request = RequestFactory().post("/")
        fresh, done = _order(public_id="AAA"), _order(public_id="BBB", accepted_email_sent_at=timezone.now())
        model_admin.confirm_received(request, [fresh, done])
        send.assert_called_once_with(fresh)
        notes = [call.args[1] for call in model_admin.message_user.call_args_list]
        self.assertTrue(any("BBB: уже подтверждён" in note for note in notes))

    @patch("market.admin.send_order_accepted_email", side_effect=OrderEmailError("в заказе нет email клиента"))
    def test_reports_reason(self, _send):
        model_admin = self._admin()
        model_admin.confirm_received(RequestFactory().post("/"), [_order(public_id="CCC")])
        self.assertIn("CCC: в заказе нет email клиента", model_admin.message_user.call_args.args[1])
