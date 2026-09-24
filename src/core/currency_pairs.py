"""Пары KRW→quote: сид, черновик из Frankfurter+ЦБ, сериализация для API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.utils import timezone
from pycbrf import ExchangeRates

from core.models import CurrencyPair

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"
RATE_QUANT = Decimal("0.0000000001")

# Стартовая сетка (этап A): quote за 1 KRW, из коммерческого прайса 77_000 ₩.
PAIR_SEED: tuple[dict[str, Any], ...] = (
    {
        "quote": "RUB",
        "name": "Российский рубль",
        "symbol": "₽",
        "rate": Decimal("0.0740779221"),
        "sort": 10,
    },
    {
        "quote": "USD",
        "name": "Доллар США",
        "symbol": "$",
        "rate": Decimal("0.0008831169"),
        "sort": 20,
    },
    {
        "quote": "EUR",
        "name": "Евро",
        "symbol": "€",
        "rate": Decimal("0.0007662338"),
        "sort": 30,
    },
    {
        "quote": "KZT",
        "name": "Казахстанский тенге",
        "symbol": "₸",
        "rate": Decimal("0.3927922078"),
        "sort": 40,
    },
    {
        "quote": "KGS",
        "name": "Киргизский сом",
        "symbol": "сом",
        "rate": Decimal("0.0766753247"),
        "sort": 50,
    },
    {
        "quote": "UZS",
        "name": "Узбекский сум",
        "symbol": "сум",
        "rate": Decimal("10.3770129870"),
        "sort": 60,
    },
)


def _q(value: Decimal | float | str) -> Decimal:
    return Decimal(str(value)).quantize(RATE_QUANT, rounding=ROUND_HALF_UP)


def seed_currency_pairs() -> int:
    """Создаёт пары, если ключей ещё нет. Существующие rate не трогает."""
    created_n = 0
    for seed in PAIR_SEED:
        _, created = CurrencyPair.objects.get_or_create(
            base="KRW",
            quote=seed["quote"],
            defaults={
                "name": seed["name"],
                "symbol": seed["symbol"],
                "rate": seed["rate"],
                "sort": seed["sort"],
                "is_active": True,
            },
        )
        if created:
            created_n += 1
    return created_n


def _fetch_frankfurter_krw(symbols: list[str]) -> dict[str, Decimal]:
    qs = ",".join(symbols)
    url = f"{FRANKFURTER_URL}?base=KRW&symbols={qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "evacode-currency/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"Frankfurter недоступен: {exc}") from exc
    rates = payload.get("rates") or {}
    out: dict[str, Decimal] = {}
    for code in symbols:
        if code in rates and rates[code]:
            out[code] = _q(rates[code])
    if not out:
        raise RuntimeError("Frankfurter не вернул курсы для KRW")
    return out


def build_draft_rates() -> dict[str, tuple[Decimal, str]]:
    """
    Черновик quote за 1 KRW.

    USD/EUR — Frankfurter (base=KRW).
    RUB — через USD × курс ЦБ USD/RUB.
    KZT/KGS/UZS — через RUB ÷ курс ЦБ (RUB за 1 единицу).
    """
    frank = _fetch_frankfurter_krw(["USD", "EUR"])
    cbr = ExchangeRates(str(datetime.now())[:10])
    rub_per_usd = Decimal(str(cbr["USD"].rate))
    if rub_per_usd <= 0:
        raise RuntimeError("ЦБ вернул нулевой курс USD")

    drafts: dict[str, tuple[Decimal, str]] = {}
    if "USD" in frank:
        drafts["USD"] = (frank["USD"], "frankfurter")
    if "EUR" in frank:
        drafts["EUR"] = (frank["EUR"], "frankfurter")

    if "USD" not in drafts:
        raise RuntimeError("Нет KRW→USD от Frankfurter — нельзя построить остальные пары")

    krw_to_rub = _q(drafts["USD"][0] * rub_per_usd)
    drafts["RUB"] = (krw_to_rub, "frankfurter+cbr")

    for code in ("KZT", "KGS", "UZS"):
        try:
            rub_per_unit = Decimal(str(cbr[code].rate))
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"ЦБ не вернул {code}: {exc}") from exc
        if rub_per_unit <= 0:
            raise RuntimeError(f"ЦБ вернул нулевой курс {code}")
        drafts[code] = (_q(krw_to_rub / rub_per_unit), "frankfurter+cbr")

    return drafts


def refresh_drafts() -> dict[str, Any]:
    """Пишет draft_rate у активных пар. Живой rate не меняет."""
    seed_currency_pairs()
    drafts = build_draft_rates()
    now = timezone.now()
    updated = []
    missing = []
    for pair in CurrencyPair.objects.filter(base="KRW", is_active=True):
        item = drafts.get(pair.quote)
        if not item:
            missing.append(pair.quote)
            continue
        rate, source = item
        pair.draft_rate = rate
        pair.draft_source = source
        pair.draft_updated_at = now
        pair.save(update_fields=["draft_rate", "draft_source", "draft_updated_at"])
        updated.append(pair.quote)
    return {
        "updated": updated,
        "missing": missing,
        "drafts": {k: str(v[0]) for k, v in drafts.items()},
        "at": now.isoformat(),
    }


def accept_drafts(*, quotes: list[str] | None = None) -> int:
    """Копирует draft_rate → rate. Если quotes задан — только эти котировки."""
    qs = CurrencyPair.objects.filter(base="KRW", is_active=True).exclude(draft_rate__isnull=True)
    if quotes:
        qs = qs.filter(quote__in=quotes)
    accepted = 0
    for pair in qs:
        pair.rate = pair.draft_rate
        pair.save(update_fields=["rate", "updated_at"])
        accepted += 1
    return accepted


def serialize_rates(*, include_inactive: bool = False) -> dict[str, Any]:
    qs = CurrencyPair.objects.filter(base="KRW").order_by("sort", "quote")
    if not include_inactive:
        qs = qs.filter(is_active=True)
    pairs = list(qs)
    updated_at = None
    if pairs:
        updated_at = max((p.updated_at for p in pairs if p.updated_at), default=None)
    return {
        "base": "KRW",
        "updated_at": updated_at.isoformat() if updated_at else None,
        "rates": [
            {
                "quote": p.quote,
                "name": p.name,
                "symbol": p.symbol,
                "rate": str(p.rate),
            }
            for p in pairs
        ],
    }
