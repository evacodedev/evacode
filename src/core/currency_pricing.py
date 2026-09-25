"""Наценка и округление продажных цен по валютам (всегда вверх)."""

from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Union

Number = Union[Decimal, int, float, str]

ZERO = Decimal("0")


def _d(value: Number) -> Decimal:
    return Decimal(str(value))


def _ceil_to_step(amount: Decimal, step: Decimal) -> Decimal:
    if amount <= ZERO:
        return ZERO
    if step <= ZERO:
        raise ValueError("step must be positive")
    return (amount / step).to_integral_value(rounding=ROUND_CEILING) * step


def round_up_half_or_99(amount: Decimal) -> Decimal:
    """Вверх до x.50 или x.99 (USD/EUR при сумме < 75)."""
    if amount <= ZERO:
        return ZERO
    whole = int(amount.to_integral_value(rounding=ROUND_FLOOR))
    for w in range(whole, whole + 4):
        for ending in (Decimal("0.50"), Decimal("0.99")):
            cand = Decimal(w) + ending
            if cand >= amount:
                return cand
    return amount


def round_up_50_or_90(amount: Decimal) -> Decimal:
    """Вверх до числа, оканчивающегося на 50 или 90 (RUB/KZT/KGS 1000–9999)."""
    if amount <= ZERO:
        return ZERO
    block = int((amount / Decimal("100")).to_integral_value(rounding=ROUND_FLOOR)) * 100
    for _ in range(8):
        for ending in (50, 90):
            cand = Decimal(block + ending)
            if cand >= amount:
                return cand
        block += 100
    return amount


def round_quote_price(quote: str, amount: Number) -> Decimal:
    """Округление продажной цены вверх по правилам валюты."""
    code = (quote or "").upper()
    raw = _d(amount)
    if raw <= ZERO:
        return ZERO

    if code in ("USD", "EUR"):
        if raw < Decimal("75"):
            return round_up_half_or_99(raw)
        if raw < Decimal("250"):
            return raw.to_integral_value(rounding=ROUND_CEILING)
        return _ceil_to_step(raw, Decimal("5"))

    if code in ("RUB", "KZT", "KGS"):
        if raw < Decimal("1000"):
            return _ceil_to_step(raw, Decimal("10"))
        if raw < Decimal("10000"):
            return round_up_50_or_90(raw)
        return _ceil_to_step(raw, Decimal("100"))

    if code == "UZS":
        return _ceil_to_step(raw, Decimal("1000"))

    if code == "KRW":
        return raw.to_integral_value(rounding=ROUND_CEILING)

    # неизвестная валюта — вверх до 0.01
    return raw.quantize(Decimal("0.01"), rounding=ROUND_CEILING)


def apply_markup(amount: Number, markup: Number) -> Decimal:
    m = _d(markup)
    if m <= ZERO:
        m = Decimal("1")
    return _d(amount) * m


def compute_commercial_rate(base_rate: Number, markup: Number) -> Decimal:
    """Исконный × коэффициент → коммерческий курс (для хранения в CurrencyPair.rate)."""
    from decimal import ROUND_HALF_UP

    return apply_markup(base_rate, markup).quantize(
        Decimal("0.0000000001"),
        rounding=ROUND_HALF_UP,
    )
