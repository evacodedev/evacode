import json
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import CurrencyPair
from market.models import SiteOrder, TBankOperation
from market.tbank import pull_recent_statement, save_operation


ACCOUNT = "40702810510000710417"
WEBHOOK = "/api/market/tbank/operations/"


def _operation(**overrides):
    payload = {
        "operationDate": "2026-09-30T08:15:00Z",
        "operationId": "64be58f9-c7fc-0027-96ba-763ec56a2317",
        "operationStatus": "Transaction",
        "accountNumber": ACCOUNT,
        "typeOfOperation": "Credit",
        "documentNumber": "175926",
        "operationAmount": 550,
        "operationCurrencyDigitalCode": "643",
        "rubleAmount": 550,
        "payPurpose": "Оплата заказа TBNK2K4R. НДС не облагается",
        "description": "",
        "payer": {
            "acct": "40817810000000000001",
            "name": "ПЕТРОВ ИВАН ИВАНОВИЧ",
            "inn": "770000000000",
        },
        "receiver": {
            "acct": ACCOUNT,
            "name": "Evacode",
            "inn": "1234567890",
        },
    }
    payload.update(overrides)
    return payload


@override_settings(
    TBANK_TOKEN="token",
    TBANK_ACCOUNT_NUMBER=ACCOUNT,
    TBANK_WEBHOOK_TOKEN="hook-secret",
    TBANK_PAYEE_NAME="Evacode",
    TBANK_INN="1234567890",
    TBANK_BANK="АО «ТБанк»",
    TBANK_BIK="044525974",
    TBANK_CORR_ACCOUNT="30101810145250000974",
)
class TBankMatchTests(TestCase):
    def setUp(self):
        CurrencyPair.objects.update_or_create(
            base="KRW",
            quote="RUB",
            defaults={
                "name": "Рубль",
                "symbol": "₽",
                "rate": Decimal("0.055"),
                "sort": 10,
                "is_active": True,
            },
        )
        self.order = SiteOrder.objects.create(
            public_id="TBNK2K4R",
            status=SiteOrder.Status.MANAGER,
            first_name="Иван Петров",
            phone="+79990001122",
            email="ivan@example.com",
            country="Россия",
            city="Москва",
            address="ул. Пример, д. 1",
            amount_krw=10000,
            amount_usd=Decimal("7.00"),
        )

    def test_statement_matches_amount_payer_and_order_number(self):
        row = save_operation(_operation(), source="statement")
        self.assertEqual(row.order_id, self.order.id)
        self.assertEqual(row.match_status, TBankOperation.Match.MATCHED)
        self.assertIn("плательщик совпал", row.match_note)

    def test_amount_mismatch_stays_visible_on_the_order(self):
        row = save_operation(_operation(operationAmount=100, rubleAmount=100), source="statement")
        self.assertEqual(row.order_id, self.order.id)
        self.assertEqual(row.match_status, TBankOperation.Match.AMOUNT_DIFFERS)

    def test_unique_amount_and_name_match_without_order_number(self):
        row = save_operation(_operation(payPurpose="Перевод собственных средств"), source="webhook")
        self.assertEqual(row.order_id, self.order.id)
        self.assertEqual(row.match_status, TBankOperation.Match.BY_PAYER)

    def test_same_amount_for_two_orders_is_not_guessed(self):
        SiteOrder.objects.create(
            public_id="ZZZZ9999",
            status=SiteOrder.Status.PENDING,
            first_name="Иван Петров",
            phone="+79990001123",
            email="ivan2@example.com",
            country="Россия",
            city="Москва",
            address="ул. Пример, д. 2",
            amount_krw=10000,
            amount_usd=Decimal("7.00"),
        )
        row = save_operation(_operation(payPurpose="Перевод"), source="statement")
        self.assertIsNone(row.order_id)
        self.assertEqual(row.match_status, TBankOperation.Match.UNMATCHED)

    def test_debit_is_stored_and_not_linked(self):
        row = save_operation(_operation(typeOfOperation="Debit"), source="statement")
        self.assertIsNone(row.order_id)

    def test_webhook_and_statement_ids_collapse_to_one_row(self):
        save_operation(_operation(), source="webhook")
        save_operation(
            _operation(operationId="other-id-from-statement"),
            source="statement",
        )
        self.assertEqual(TBankOperation.objects.count(), 1)
        row = TBankOperation.objects.get()
        self.assertEqual(row.statement_operation_id, "other-id-from-statement")

    def test_webhook_requires_bearer_and_bank_ip(self):
        body = json.dumps(_operation())
        denied = self.client.post(WEBHOOK, data=body, content_type="application/json")
        self.assertEqual(denied.status_code, 401)

        wrong_ip = self.client.post(
            WEBHOOK,
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer hook-secret",
            HTTP_X_FORWARDED_FOR="1.2.3.4",
        )
        self.assertEqual(wrong_ip.status_code, 403)

        ok = self.client.post(
            WEBHOOK,
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer hook-secret",
            HTTP_X_FORWARDED_FOR="91.194.226.234",
        )
        self.assertEqual(ok.status_code, 200, ok.content)
        self.assertEqual(TBankOperation.objects.count(), 1)
        again = self.client.post(
            WEBHOOK,
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer hook-secret",
            HTTP_X_FORWARDED_FOR="91.194.226.234",
        )
        self.assertEqual(again.status_code, 200)
        self.assertEqual(TBankOperation.objects.count(), 1)

    @patch("market.tbank.requests.get")
    def test_statement_follows_cursor(self, get):
        first = _operation()
        second = _operation(operationId="second-id", documentNumber="175927", payPurpose="другое")
        get.side_effect = [
            _response({"operations": [first], "nextCursor": "cursor-1"}),
            _response({"operations": [second], "nextCursor": ""}),
        ]
        saved = pull_recent_statement(days=2)
        self.assertEqual(saved, 2)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["cursor"], "cursor-1")
        self.assertEqual(get.call_args_list[0].kwargs["headers"]["Authorization"], "Bearer token")

    def test_consultant_marks_paid_without_export(self):
        save_operation(_operation(), source="statement")
        user = get_user_model().objects.create_superuser("boss", "boss@example.com", "password")
        self.client.force_login(user)
        url = reverse("admin:market_siteorder_mark_bank_paid", args=[self.order.pk])
        with patch("market.business_ru_orders.export_paid_order") as export:
            response = self.client.post(url)
            export.assert_not_called()
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, SiteOrder.Status.PAID)
        self.assertIsNotNone(self.order.paid_at)
        self.assertEqual(self.order.business_ru_order_id, "")


def _response(payload, status=200):
    response = type("Response", (), {})()
    response.status_code = status
    response.json = lambda: payload
    response.text = json.dumps(payload)
    return response


class TBankStatementDateTests(TestCase):
    def test_operation_date_is_parsed(self):
        row = save_operation(_operation(payPurpose="без заказа", payer={"name": "Кто-то"}), source="statement")
        self.assertEqual(
            row.operation_date,
            datetime(2026, 9, 30, 8, 15, tzinfo=dt_timezone.utc),
        )
