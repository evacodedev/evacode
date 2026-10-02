"""Заказы через консультантов: роль, сверка оплат, точный поиск клиента."""

import re
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth.models import User
from django.db.models import Sum

from core.currency_pairs import convert_krw_amount, get_quote_rate
from core.models import AccountProfile, CurrencyPair

from .models import Consultant, SiteOrder

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOOKUP_LIMIT_PER_HOUR = 30
LOOKUP_MIN_PHONE_DIGITS = 7
HOUSE_FIRST_DESTINATIONS = {"US", "GB", "FR"}


def active_consultant(user) -> Consultant | None:
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return (
        Consultant.objects.select_related("user")
        .filter(user_id=user.pk, is_active=True)
        .exclude(business_ru_employee_id="")
        .first()
    )


def available_currencies() -> list[dict]:
    rows = [{"code": "KRW", "name": "Корейская вона", "symbol": "₩", "rate": "1"}]
    for pair in CurrencyPair.objects.filter(base="KRW", is_active=True).exclude(quote="KRW").order_by("sort", "quote"):
        if pair.rate and pair.rate > 0:
            rows.append(
                {
                    "code": pair.quote,
                    "name": pair.name or pair.quote,
                    "symbol": pair.symbol or "",
                    "rate": str(get_quote_rate(pair.quote)),
                }
            )
    return rows


def currency_codes() -> set[str]:
    return {row["code"] for row in available_currencies()}


def currency_rate(code: str) -> Decimal:
    """Коммерческий курс: валюта за 1 ₩."""
    code = (code or "KRW").upper()
    if code == "KRW":
        return Decimal("1")
    return get_quote_rate(code)


def amount_to_krw(amount: Decimal, code: str) -> tuple[int, Decimal]:
    rate = currency_rate(code)
    krw = (Decimal(str(amount)) / rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(krw), rate


def krw_to_display(amount_krw: int, code: str) -> tuple[Decimal, Decimal]:
    code = (code or "KRW").upper()
    return convert_krw_amount(amount_krw, code), currency_rate(code)


def order_paid_krw(order: SiteOrder) -> int:
    if not order.pk:
        return 0
    return int(order.payments.aggregate(total=Sum("amount_krw"))["total"] or 0)


def payment_check(order: SiteOrder) -> dict:
    """Сверка по курсу на момент записи каждой оплаты. Порога нет: любая нехватка — недоплата."""
    paid = order_paid_krw(order)
    shortfall = max(order.amount_krw - paid, 0)
    currency = (order.display_currency or "KRW").upper()
    last = order.payments.order_by("-created_at", "-id").first() if order.pk else None
    if last is not None:
        currency = last.currency
    shortfall_display = None
    if shortfall:
        try:
            amount, _rate = krw_to_display(shortfall, currency)
        except ValueError:
            amount, currency = Decimal(shortfall), "KRW"
        shortfall_display = {"amount": str(amount), "currency": currency}
    return {
        "amount_krw": order.amount_krw,
        "paid_krw": paid,
        "shortfall_krw": shortfall,
        "overpaid_krw": max(paid - order.amount_krw, 0),
        "shortfall_display": shortfall_display,
        "has_payments": order.payments.exists() if order.pk else False,
    }


def normalize_lookup(query: str) -> tuple[str, str] | None:
    raw = (query or "").strip()
    if "@" in raw:
        email = raw.lower()
        return ("email", email) if EMAIL_RE.match(email) else None
    if re.search(r"[^\d\s()+\-.]", raw):
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < LOOKUP_MIN_PHONE_DIGITS:
        return None
    return ("phone", digits)


def _digits(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _address_line(country_code: str, street: str, house: str, apartment: str) -> str:
    street, house, apartment = (street or "").strip(), (house or "").strip(), (apartment or "").strip()
    parts = [house, street] if (country_code or "").upper() in HOUSE_FIRST_DESTINATIONS else [street, house]
    line = " ".join(part for part in parts if part)
    return ", ".join(part for part in [line, f"Apt. {apartment}" if apartment else ""] if part)


def _client_from_order(order: SiteOrder) -> dict:
    return {
        "first_name": order.first_name,
        "phone": order.phone,
        "email": order.email,
        "shipping_method": order.shipping_method or "ems",
        "destination": order.shipping_destination or "",
        "country": order.country,
        "city": order.city if order.shipping_method != "pickup" else "",
        "address": order.address if order.shipping_method != "pickup" else "",
        "postal_code": order.postal_code,
    }


def _client_from_user(user: User) -> dict:
    profile = getattr(user, "account_profile", None)
    address = user.account_addresses.order_by("id").first()
    data = {
        "first_name": user.get_full_name() or "",
        "phone": profile.phone if profile else "",
        "email": user.email or "",
        "shipping_method": "ems",
        "destination": "",
        "country": "",
        "city": "",
        "address": "",
        "postal_code": "",
    }
    if address is not None:
        data.update(
            {
                "destination": address.country_code or "",
                "country": address.country or "",
                "city": address.city,
                "address": _address_line(address.country_code, address.street, address.house, address.apartment),
                "postal_code": address.postal_code,
            }
        )
    return data


def find_client(kind: str, value: str) -> dict | None:
    """Только точное совпадение email или всех цифр телефона. Черновики консультантов не источник."""
    orders = SiteOrder.objects.exclude(status=SiteOrder.Status.CONSULTANT_DRAFT)
    if kind == "email":
        order = orders.filter(email__iexact=value).order_by("-created_at").first()
        if order is not None:
            return _client_from_order(order)
        user = (
            User.objects.filter(email__iexact=value).first()
            or User.objects.filter(username__iexact=value).first()
        )
        return _client_from_user(user) if user is not None else None

    order = orders.filter(phone_digits=value).order_by("-created_at").first()
    if order is not None:
        return _client_from_order(order)
    for profile in AccountProfile.objects.select_related("user").exclude(phone=""):
        if _digits(profile.phone) == value:
            return _client_from_user(profile.user)
    return None
