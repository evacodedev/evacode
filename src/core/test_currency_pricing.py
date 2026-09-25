from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from core.currency_pairs import convert_krw_amount, seed_currency_pairs, storefront_currency_list
from core.currency_pricing import compute_commercial_rate, round_quote_price
from core.models import CurrencyPair


class RoundQuotePriceTests(SimpleTestCase):
    def test_usd_eur_under_75_half_or_99(self):
        self.assertEqual(round_quote_price("USD", "20.31"), Decimal("20.50"))
        self.assertEqual(round_quote_price("USD", "31.55"), Decimal("31.99"))
        self.assertEqual(round_quote_price("EUR", "20.50"), Decimal("20.50"))
        self.assertEqual(round_quote_price("EUR", "31.99"), Decimal("31.99"))

    def test_usd_eur_75_to_250_ceil_to_1(self):
        self.assertEqual(round_quote_price("USD", "120.1"), Decimal("121"))
        self.assertEqual(round_quote_price("EUR", "75.01"), Decimal("76"))
        self.assertEqual(round_quote_price("USD", "249.01"), Decimal("250"))

    def test_usd_eur_over_250_ceil_to_5(self):
        self.assertEqual(round_quote_price("USD", "301.45"), Decimal("305"))
        self.assertEqual(round_quote_price("USD", "278.99"), Decimal("280"))
        self.assertEqual(round_quote_price("EUR", "250.01"), Decimal("255"))

    def test_rub_kzt_kgs_under_1000(self):
        self.assertEqual(round_quote_price("RUB", "421"), Decimal("430"))
        self.assertEqual(round_quote_price("KZT", "999"), Decimal("1000"))
        self.assertEqual(round_quote_price("KGS", "10"), Decimal("10"))

    def test_rub_kzt_kgs_1000_to_9999_50_or_90(self):
        self.assertEqual(round_quote_price("RUB", "1000"), Decimal("1050"))
        self.assertEqual(round_quote_price("KZT", "1051"), Decimal("1090"))
        self.assertEqual(round_quote_price("KGS", "1190"), Decimal("1190"))
        self.assertEqual(round_quote_price("RUB", "1191"), Decimal("1250"))

    def test_rub_kzt_kgs_from_10000(self):
        self.assertEqual(round_quote_price("RUB", "10000"), Decimal("10000"))
        self.assertEqual(round_quote_price("KZT", "10001"), Decimal("10100"))

    def test_uzs_ceil_1000(self):
        self.assertEqual(round_quote_price("UZS", "1"), Decimal("1000"))
        self.assertEqual(round_quote_price("UZS", "1500"), Decimal("2000"))
        self.assertEqual(round_quote_price("UZS", "5000"), Decimal("5000"))


class ConvertCommercialTests(TestCase):
    def test_convert_uses_commercial_rate_only(self):
        seed_currency_pairs()
        CurrencyPair.objects.filter(quote="USD").update(rate=Decimal("0.00107"))
        # 20000 × 0.00107 = 21.4 → 21.50; коэффициент в операциях не участвует
        self.assertEqual(convert_krw_amount(20000, "USD"), Decimal("21.50"))

    def test_storefront_curr_is_commercial(self):
        seed_currency_pairs()
        CurrencyPair.objects.filter(quote="RUB").update(rate=Decimal("0.05275"))
        rows = storefront_currency_list(["RUB"])
        by_code = {row["value"]: row for row in rows}
        self.assertAlmostEqual(by_code["RUB"]["curr"], 0.05275)
        self.assertNotIn("markup", by_code["RUB"])

    def test_commercial_from_api_times_markup(self):
        self.assertEqual(
            compute_commercial_rate(Decimal("0.001"), Decimal("1.07")),
            Decimal("0.0010700000"),
        )
