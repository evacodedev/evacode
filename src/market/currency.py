from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from core.models import Currency
from pycbrf import ExchangeRates


def _admin_rate(key: str) -> Decimal:
    row = Currency.objects.filter(key=key).order_by("id").first()
    if row is None or not row.value:
        raise ValueError(f"Не задан курс {key} в админке")
    return Decimal(str(row.value))


def krw_to_usd(amount_krw: int | Decimal) -> tuple[Decimal, Decimal]:
    """Convert KRW to USD using the same formula as the storefront.

    Returns (usd_amount, krw_per_usd snapshot).
    """
    krw_per_rub = _admin_rate("krw-rub-eur")
    rates = ExchangeRates(str(datetime.now())[:10])
    rub_per_usd = Decimal(str(rates["USD"].rate))
    if rub_per_usd <= 0:
        raise ValueError("ЦБ вернул нулевой курс USD")

    krw_amount = Decimal(str(amount_krw))
    usd = (krw_amount / krw_per_rub / rub_per_usd).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    snapshot = (krw_per_rub * rub_per_usd).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    return usd, snapshot
