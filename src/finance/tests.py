import json
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase

from finance.models import InvoiceTossPayments
from finance.views import _build_confirm_error_message, _confirmation_window_expired, confirm_payment


class InvoiceTossPaymentsPayloadTests(SimpleTestCase):
    def _build_invoice(self, payment_type):
        return InvoiceTossPayments(
            amount=Decimal("10.00"),
            description="EVACODE Order",
            customer_name="Test User",
            customer_phone="+70000000000",
            customer_email="test@example.com",
            manager_name="Manager",
            payment_link="",
            payment_type=payment_type,
        )

    def test_card_payment_type_builds_card_payload(self):
        invoice = self._build_invoice(InvoiceTossPayments.PaymentType.CARD)

        payload = invoice._build_toss_payload(
            order_id="inv-1",
            success_url="https://example.com/success",
            fail_url="https://example.com/fail",
        )

        self.assertEqual(payload["method"], InvoiceTossPayments.PaymentType.CARD)
        self.assertNotIn("provider", payload)
        self.assertNotIn("currency", payload)

    def test_foreign_payment_type_builds_paypal_payload(self):
        invoice = self._build_invoice(InvoiceTossPayments.PaymentType.FOREIGN)

        payload = invoice._build_toss_payload(
            order_id="inv-2",
            success_url="https://example.com/success",
            fail_url="https://example.com/fail",
        )

        self.assertEqual(payload["method"], InvoiceTossPayments.PaymentType.FOREIGN)
        self.assertEqual(payload["provider"], "PAYPAL")
        self.assertEqual(payload["currency"], "USD")

    def test_unsupported_payment_type_raises_error(self):
        invoice = self._build_invoice("BANK_TRANSFER")

        with self.assertRaisesMessage(ValueError, "Unsupported TOSS payment type"):
            invoice._build_toss_payload(
                order_id="inv-3",
                success_url="https://example.com/success",
                fail_url="https://example.com/fail",
            )


class ConfirmPaymentHelpersTests(SimpleTestCase):
    def test_confirmation_window_expired_after_ten_minutes(self):
        payment_data = {"requestedAt": "2026-03-18T22:19:43+09:00"}
        mocked_now = datetime(2026, 3, 18, 17, 2, 36, tzinfo=ZoneInfo("Europe/Moscow"))

        with patch("finance.views.timezone.now", return_value=mocked_now):
            self.assertTrue(_confirmation_window_expired(payment_data))

    def test_build_confirm_error_message_for_expired_in_progress_payment(self):
        payment_data = {"status": "IN_PROGRESS", "requestedAt": "2026-03-18T22:19:43+09:00"}
        mocked_now = datetime(2026, 3, 18, 17, 2, 36, tzinfo=ZoneInfo("Europe/Moscow"))

        with patch("finance.views.timezone.now", return_value=mocked_now):
            message = _build_confirm_error_message("Base error", payment_data)

        self.assertIn("10-минутное окно подтверждения уже истекло", message)

    def test_build_confirm_error_message_for_fresh_in_progress_payment(self):
        payment_data = {"status": "IN_PROGRESS", "requestedAt": "2026-03-18T22:19:43+09:00"}
        mocked_now = datetime(2026, 3, 18, 16, 21, 0, tzinfo=ZoneInfo("Europe/Moscow"))

        with patch("finance.views.timezone.now", return_value=mocked_now):
            message = _build_confirm_error_message("Base error", payment_data)

        self.assertIn("Повторите подтверждение через несколько секунд", message)


class ConfirmPaymentViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _build_response(self, ok, status_code, payload):
        response = Mock()
        response.ok = ok
        response.status_code = status_code
        response.json.return_value = payload
        response.text = json.dumps(payload, ensure_ascii=False)
        return response

    @patch("finance.views.render", side_effect=lambda request, template, context: context)
    @patch("finance.views.InvoiceTossPayments")
    def test_unpaid_invoice_requires_callback_params(self, invoice_model, _render_mock):
        invoice = Mock(
            amount=Decimal("10.00"),
            is_paid=False,
            order_id="inv-1",
            payment_id="ready-payment-key",
            status="READY",
        )
        invoice_model.objects.filter.return_value.first.return_value = invoice

        request = self.factory.get("/api/invoice/confirm/inv-1/")

        response = confirm_payment(request, "inv-1")

        self.assertEqual(response["error_code"], "MISSING_CONFIRM_PARAMS")
        self.assertIn("successUrl", response["error_message"])

    @patch("finance.views.render", side_effect=lambda request, template, context: context)
    @patch("finance.views.InvoiceTossPayments")
    def test_paid_invoice_can_open_success_page_without_callback_params(self, invoice_model, _render_mock):
        invoice = Mock(
            amount=Decimal("10.00"),
            is_paid=True,
            order_id="inv-1",
            payment_id="confirmed-payment-key",
            status="DONE",
        )
        invoice_model.objects.filter.return_value.first.return_value = invoice

        request = self.factory.get("/api/invoice/confirm/inv-1/")

        response = confirm_payment(request, "inv-1")

        self.assertEqual(response["payment_key"], "confirmed-payment-key")
        self.assertEqual(response["amount"], Decimal("10.00"))

    @patch("finance.views.requests.post")
    @patch("finance.views.render", side_effect=lambda request, template, context: context)
    @patch("finance.views.InvoiceTossPayments")
    def test_successful_confirm_response_is_saved(self, invoice_model, _render_mock, post_mock):
        invoice = Mock(
            amount=Decimal("10.00"),
            confirm_response=None,
            is_paid=False,
            order_id="inv-1",
            payment_id="ready-payment-key",
            status="READY",
        )
        invoice_model.objects.filter.return_value.first.return_value = invoice
        post_mock.return_value = self._build_response(
            ok=True,
            status_code=200,
            payload={"paymentKey": "confirmed-payment-key", "status": "DONE"},
        )

        request = self.factory.get(
            "/api/invoice/confirm/inv-1/",
            {"paymentKey": "confirmed-payment-key", "amount": "10", "orderId": "inv-1"},
        )

        response = confirm_payment(request, "inv-1")
        saved_response = json.loads(invoice.confirm_response)

        self.assertEqual(saved_response["status_code"], 200)
        self.assertTrue(saved_response["ok"])
        self.assertEqual(saved_response["body"]["status"], "DONE")
        invoice.save.assert_called_once_with(
            update_fields=["payment_id", "status", "is_paid", "confirm_response", "updated_at"]
        )
        self.assertEqual(response["payment_key"], "confirmed-payment-key")

    @patch("finance.views._fetch_payment", return_value=(None, ("PAYMENT_LOOKUP_ERROR", "lookup failed")))
    @patch("finance.views.requests.post")
    @patch("finance.views.render", side_effect=lambda request, template, context: context)
    @patch("finance.views.InvoiceTossPayments")
    def test_failed_confirm_response_is_saved(self, invoice_model, _render_mock, post_mock, _fetch_payment_mock):
        invoice = Mock(
            amount=Decimal("10.00"),
            confirm_response=None,
            is_paid=False,
            order_id="inv-1",
            payment_id="ready-payment-key",
            status="READY",
        )
        invoice_model.objects.filter.return_value.first.return_value = invoice
        post_mock.return_value = self._build_response(
            ok=False,
            status_code=401,
            payload={"code": "INVALID_API_KEY", "message": "Incorrect secret key."},
        )

        request = self.factory.get(
            "/api/invoice/confirm/inv-1/",
            {"paymentKey": "ready-payment-key", "amount": "10", "orderId": "inv-1"},
        )

        response = confirm_payment(request, "inv-1")
        saved_response = json.loads(invoice.confirm_response)

        self.assertEqual(saved_response["status_code"], 401)
        self.assertFalse(saved_response["ok"])
        self.assertEqual(saved_response["body"]["code"], "INVALID_API_KEY")
        invoice.save.assert_called_once_with(update_fields=["status", "is_paid", "confirm_response", "updated_at"])
        self.assertEqual(response["error_code"], "INVALID_API_KEY")
