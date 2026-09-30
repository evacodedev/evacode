from django.test import SimpleTestCase, override_settings

from market.business_ru_orders import (
    BusinessRuOrderError,
    _ensure_order_reference_fields,
    _order_payment_type_id,
    _order_reference_fields,
)
from market.models import SiteOrder


class FakeClient:
    def __init__(self, record=None, fail_put=False):
        self.record = record or {}
        self.fail_put = fail_put
        self.calls = []

    def request(self, method, model, params=None):
        self.calls.append((method, model, params))
        if method == "get":
            return {"result": [self.record]}
        if self.fail_put:
            raise BusinessRuOrderError("boom")
        return {"result": {"id": params["id"]}}


def _paypal_order(**extra):
    return SiteOrder(paypal_capture_id="CAP1", business_ru_order_id="2877350", **extra)


@override_settings(BUSINESS_RU_PAYPAL_PAYMENT_TYPE_ID="353536", BUSINESS_RU_REQUEST_SOURCE_ID="2")
class OrderReferenceFieldsTests(SimpleTestCase):
    def test_paypal_order_gets_source_and_paypal_type(self):
        self.assertEqual(
            _order_reference_fields(_paypal_order()),
            {"request_source_id": "2", "payment_type_id": "353536"},
        )

    def test_order_without_paypal_gets_only_source(self):
        self.assertEqual(_order_reference_fields(SiteOrder()), {"request_source_id": "2"})
        self.assertEqual(_order_payment_type_id(SiteOrder()), "")

    @override_settings(BUSINESS_RU_PAYPAL_PAYMENT_TYPE_ID="", BUSINESS_RU_REQUEST_SOURCE_ID="")
    def test_empty_settings_disable_fields(self):
        self.assertEqual(_order_reference_fields(_paypal_order()), {})

    def test_existing_order_gets_only_missing_fields(self):
        client = FakeClient({"id": "2877350", "request_source_id": 2, "payment_type_id": None})
        _ensure_order_reference_fields(client, _paypal_order())
        self.assertIn(
            ("put", "customerorders", {"id": "2877350", "payment_type_id": "353536"}),
            client.calls,
        )

    def test_existing_order_with_same_values_is_not_touched(self):
        client = FakeClient({"id": "2877350", "request_source_id": "2", "payment_type_id": 353536})
        _ensure_order_reference_fields(client, _paypal_order())
        self.assertEqual([call[0] for call in client.calls], ["get"])

    def test_put_error_does_not_break_export(self):
        client = FakeClient({"id": "2877350"}, fail_put=True)
        _ensure_order_reference_fields(client, _paypal_order())
