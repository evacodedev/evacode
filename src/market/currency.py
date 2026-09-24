from decimal import Decimal, ROUND_HALF_UP

from core.currency_pairs import get_quote_rate


def krw_to_usd(amount_krw: int | Decimal) -> tuple[Decimal, Decimal]:
    """Convert KRW to USD from the official KRW/USD currency pair.

    Returns (usd_amount, krw_per_usd snapshot).
    """
    usd_per_krw = get_quote_rate("USD")
    krw_amount = Decimal(str(amount_krw))
    usd = (krw_amount * usd_per_krw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    snapshot = (Decimal("1") / usd_per_krw).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    return usd, snapshot
