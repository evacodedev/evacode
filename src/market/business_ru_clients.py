"""Поиск контрагента Business.Ru для консультанта: только точный email или телефон, без частичных совпадений."""

import logging
from concurrent.futures import ThreadPoolExecutor

import requests

from .business_ru_orders import BusinessRuOrderClient, BusinessRuOrderError

logger = logging.getLogger(__name__)

MAX_MATCHES = 3
CONTACT_PHONE = "1"
CONTACT_ADDRESS = "3"
CONTACT_EMAIL = "4"
BR_ERRORS = (BusinessRuOrderError, requests.RequestException, ValueError)


def _digits(value) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def phone_variants(phone_digits: str) -> list[str]:
    """В BR телефон хранится цифрами, но по-разному: 7… или 8… для РФ/КЗ, 8210… или 010… для Кореи."""
    d = _digits(phone_digits)
    if not d:
        return []
    variants = [d]
    if len(d) == 11 and d[0] == "7":
        variants.append("8" + d[1:])
    elif len(d) == 11 and d[0] == "8" and not d.startswith("82"):
        variants.append("7" + d[1:])
    elif len(d) == 10 and d[0] == "9":
        variants += ["7" + d, "8" + d]
    if d.startswith("82") and len(d) in (11, 12):
        variants.append("0" + d[2:])
    elif d.startswith("010") and len(d) in (10, 11):
        variants.append("82" + d[1:])
    return list(dict.fromkeys(variants))


def _email_variants(email: str) -> list[str]:
    raw = str(email or "").strip()
    return list(dict.fromkeys(v for v in (raw, raw.lower()) if v))


def _partners(client: BusinessRuOrderClient, params: dict) -> list[dict]:
    rows = client.request("get", "partners", params).get("result") or []
    return [row for row in rows if isinstance(row, dict) and not _is_true(row.get("deleted"))]


def _is_true(value) -> bool:
    return str(value).strip().lower() in ("1", "true")


def _search(client: BusinessRuOrderClient, email: str, phone_digits: str) -> dict[str, dict]:
    """id контрагента → {row, by_email, by_phone}. Запросы идут параллельно: каждый ~0,7 с."""
    jobs = [("email", {"email": value}) for value in _email_variants(email)]
    jobs += [("phone", {"phone": value}) for value in phone_variants(phone_digits)]
    found: dict[str, dict] = {}
    if not jobs:
        return found
    with ThreadPoolExecutor(max_workers=min(4, len(jobs))) as pool:
        results = list(pool.map(lambda job: (job[0], _partners(client, job[1])), jobs))
    for kind, rows in results:
        for row in rows:
            pid = str(row.get("id") or "")
            if not pid:
                continue
            entry = found.setdefault(pid, {"row": row, "by_email": False, "by_phone": False})
            entry["by_" + kind] = True
    return found


def _contacts(client: BusinessRuOrderClient, partner_id: str) -> list[dict]:
    rows = client.request("get", "partnercontactinfo", {"partner_id": partner_id}).get("result") or []
    return [row for row in rows if isinstance(row, dict) and not _is_true(row.get("deleted"))]


def _last_order(client: BusinessRuOrderClient, partner_id: str) -> tuple[int, dict | None]:
    """Заказы BR отдаются по возрастанию id: последний — на последней странице по одному."""
    count_payload = client.request("get", "customerorders", {"partner_id": partner_id, "count_only": 1}).get("result")
    count = int((count_payload or {}).get("count") or 0) if isinstance(count_payload, dict) else int(count_payload or 0)
    if not count:
        return 0, None
    rows = client.request("get", "customerorders", {"partner_id": partner_id, "limit": 1, "page": count}).get("result") or []
    return count, (rows[-1] if rows else None)


def _card(client: BusinessRuOrderClient, pid: str, entry: dict) -> dict:
    row = entry["row"]
    contacts = _contacts(client, pid)
    orders_count, last = _last_order(client, pid)

    def by_type(type_id: str) -> list[str]:
        values = (
            str(item.get("contact_info") or "").strip()
            for item in contacts
            if str(item.get("contact_info_type_id")) == type_id
        )
        return list(dict.fromkeys(value for value in values if value))

    address_candidates = [
        str((last or {}).get("delivery_address") or "").strip(),
        *by_type(CONTACT_ADDRESS),
        str(row.get("address_actual") or "").strip(),
        str(row.get("address_legal") or "").strip(),
    ]
    return {
        "id": pid,
        "name": str(row.get("name") or "").strip(),
        "phones": by_type(CONTACT_PHONE),
        "emails": by_type(CONTACT_EMAIL),
        "address": next((value for value in address_candidates if value), ""),
        "orders_count": orders_count,
        "last_order": (
            {"number": str(last.get("number") or ""), "date": str(last.get("date") or "")[:10]} if last else None
        ),
        "match": "+".join(kind for kind in ("email", "phone") if entry["by_" + kind]),
    }


def find_partner_matches(client: BusinessRuOrderClient, email: str, phone_digits: str) -> tuple[list[dict], int]:
    """Не больше MAX_MATCHES карточек: сначала совпавшие и по email, и по телефону, потом с большим числом заказов."""
    found = _search(client, email, phone_digits)
    if not found:
        return [], 0
    items = sorted(found.items(), key=lambda item: (item[1]["by_email"] and item[1]["by_phone"], item[1]["by_email"]), reverse=True)
    picked = items[: MAX_MATCHES * 2]
    with ThreadPoolExecutor(max_workers=min(3, len(picked))) as pool:
        cards = list(pool.map(lambda item: _card(client, item[0], item[1]), picked))
    cards.sort(key=lambda card: (card["match"] == "email+phone", "email" in card["match"], card["orders_count"]), reverse=True)
    return cards[:MAX_MATCHES], len(found)


def lookup_business_ru(email: str, phone_digits: str) -> dict:
    try:
        client = BusinessRuOrderClient()
        matches, total = find_partner_matches(client, email, phone_digits)
    except BR_ERRORS as exc:
        logger.warning("Поиск клиента в Business.Ru не удался: %s", exc)
        return {"matches": [], "total": 0, "error": "Система заказов EvaCode не ответила, проверить клиента там не удалось"}
    return {"matches": matches, "total": total, "error": ""}


def partner_has_contact(client: BusinessRuOrderClient, partner_id: str, email: str, phone_digits: str) -> bool:
    """Выбранный консультантом контрагент годится, только если у него есть телефон или email клиента."""
    wanted_email = str(email or "").strip().lower()
    wanted_phones = set(phone_variants(phone_digits))
    for item in _contacts(client, partner_id):
        type_id = str(item.get("contact_info_type_id"))
        if type_id == CONTACT_EMAIL and wanted_email and str(item.get("contact_info") or "").strip().lower() == wanted_email:
            return True
        if type_id == CONTACT_PHONE and wanted_phones and str(item.get("phone") or "") in wanted_phones:
            return True
    return False
