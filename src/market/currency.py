from decimal import Decimal

from core.currency_pairs import convert_krw_amount, get_quote_rate


def krw_to_usd(amount_krw: int | Decimal) -> tuple[Decimal, Decimal]:
    """Convert KRW to USD by commercial rate, round up by USD rules.

    Returns (usd_amount, krw_per_usd snapshot from commercial rate).
    """
    usd_per_krw = get_quote_rate("USD")
    usd = convert_krw_amount(amount_krw, "USD")
    snapshot = (Decimal("1") / usd_per_krw).quantize(Decimal("0.00000001"))
    return usd, snapshot
