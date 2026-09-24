from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from core.currency_pairs import (
    accept_drafts,
    build_draft_rates,
    get_quote_rate,
    refresh_drafts,
    seed_currency_pairs,
    serialize_rates,
    storefront_currency_list,
)
from core.models import CurrencyPair
from market.currency import krw_to_usd


class CurrencyPairsServiceTests(TestCase):
    def test_seed_creates_expected_quotes(self):
        CurrencyPair.objects.all().delete()
        n = seed_currency_pairs()
        self.assertEqual(n, 6)
        self.assertEqual(CurrencyPair.objects.filter(base="KRW").count(), 6)
        self.assertEqual(seed_currency_pairs(), 0)

    def test_serialize_rates_shape(self):
        seed_currency_pairs()
        payload = serialize_rates()
        self.assertEqual(payload["base"], "KRW")
        quotes = {row["quote"] for row in payload["rates"]}
        self.assertTrue({"RUB", "USD", "EUR", "KZT", "KGS", "UZS"} <= quotes)
        rub = next(r for r in payload["rates"] if r["quote"] == "RUB")
        self.assertIn("rate", rub)
        self.assertTrue(Decimal(rub["rate"]) > 0)

    def test_storefront_list_uses_pair_rates(self):
        seed_currency_pairs()
        CurrencyPair.objects.filter(quote="RUB").update(rate=Decimal("0.0740779221"))
        rows = storefront_currency_list(["RUB", "USD"])
        by_code = {row["value"]: row for row in rows}
        self.assertEqual(by_code["KRW"]["curr"], 1)
        self.assertAlmostEqual(by_code["RUB"]["curr"], 0.0740779221)
        self.assertEqual(by_code["RUB"]["locale"], "ru")

    def test_krw_to_usd_from_pair(self):
        seed_currency_pairs()
        CurrencyPair.objects.filter(quote="USD").update(rate=Decimal("0.0008831169"))
        usd, snapshot = krw_to_usd(77000)
        self.assertEqual(usd, Decimal("68.00"))
        self.assertGreater(snapshot, 0)

    @patch("core.currency_pairs._fetch_frankfurter_krw")
    @patch("core.currency_pairs.ExchangeRates")
    def test_refresh_and_accept_drafts(self, exchange_cls, frankfurter):
        seed_currency_pairs()
        frankfurter.return_value = {
            "USD": Decimal("0.0008"),
            "EUR": Decimal("0.0007"),
        }

        class FakeRate:
            def __init__(self, rate):
                self.rate = rate

        class FakeRates:
            def __getitem__(self, code):
                return {
                    "USD": FakeRate(Decimal("80")),
                    "KZT": FakeRate(Decimal("0.2")),
                    "KGS": FakeRate(Decimal("1")),
                    "UZS": FakeRate(Decimal("0.01")),
                }[code]

        exchange_cls.return_value = FakeRates()

        drafts = build_draft_rates()
        self.assertEqual(drafts["USD"][0], Decimal("0.0008000000"))
        self.assertEqual(drafts["RUB"][0], Decimal("0.0640000000"))
        self.assertEqual(drafts["KZT"][0], Decimal("0.3200000000"))

        result = refresh_drafts()
        self.assertIn("USD", result["updated"])
        pair = CurrencyPair.objects.get(quote="USD")
        old_rate = pair.rate
        self.assertEqual(pair.draft_rate, Decimal("0.0008000000"))

        accepted = accept_drafts(quotes=["USD"])
        self.assertEqual(accepted, 1)
        pair.refresh_from_db()
        self.assertEqual(pair.rate, Decimal("0.0008000000"))
        self.assertNotEqual(pair.rate, old_rate)
        self.assertEqual(get_quote_rate("USD"), Decimal("0.0008000000"))


class CurrencyPairsApiTests(TestCase):
    def test_public_pairs_endpoint(self):
        seed_currency_pairs()
        response = self.client.get("/api/core/currency-pairs/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["base"], "KRW")
        self.assertGreaterEqual(len(data["rates"]), 6)

    def test_storefront_currencies_endpoint(self):
        seed_currency_pairs()
        CurrencyPair.objects.filter(quote="RUB").update(rate=Decimal("0.05"))
        response = self.client.get("/api/core/currencies/")
        self.assertEqual(response.status_code, 200)
        by_code = {row["value"]: row for row in response.json()["currencies"]}
        self.assertEqual(by_code["KRW"]["curr"], 1)
        self.assertAlmostEqual(by_code["RUB"]["curr"], 0.05)
