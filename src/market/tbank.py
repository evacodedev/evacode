"""Выписка Т-Банка и сверка входящего платежа с заказом.

Официальный метод: GET /api/v1/statement
https://business.tbank.ru/openapi/api/v1/statement

Вебхук «Операция по счету» (eventType oper-feed-operation) присылает ту же операцию.
OperationId вебхука может не совпадать с OperationId выписки — дубли склеиваются
по номеру документа, сумме, времени и назначению.
"""

from __future__ import annotations

import hmac
import logging
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.utils import timezone

from core.currency_pairs import convert_krw_amount

from .models import PUBLIC_ID_ALPHABET, SiteOrder, TBankOperation

logger = logging.getLogger(__name__)

STATEMENT_PATH = "/api/v1/statement"
# IP, с которых Т-Банк шлёт вебхук «Операция по счету».
WEBHOOK_IPS = frozenset(
    {
        "212.233.80.7",
        "91.218.132.2",
        "91.194.226.234",
        "91.194.226.235",
        "91.194.226.250",
        "91.194.226.251",
    }
)
OPEN_STATUSES = (SiteOrder.Status.PENDING, SiteOrder.Status.MANAGER)
_ID_RE = re.compile(rf"(?<![{PUBLIC_ID_ALPHABET}])([{PUBLIC_ID_ALPHABET}]{{8}})(?![{PUBLIC_ID_ALPHABET}])")
_TOKEN_RE = re.compile(r"[^a-zа-яё0-9]+", re.IGNORECASE)


class TBankError(Exception):
    pass


def _pick(data, *names):
    if not isinstance(data, dict):
        return None
    for name in names:
        if name in data and data[name] not in (None, ""):
            return data[name]
    folded = {str(key).lower(): value for key, value in data.items()}
    for name in names:
        value = folded.get(name.lower())
        if value not in (None, ""):
            return value
    return None


def _text(value) -> str:
    return str(value or "").strip()


def _money(value) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def _parse_dt(value):
    text = _text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, dt_timezone.utc)
    return parsed


def _party(data, key: str) -> dict:
    raw = _pick(data, key)
    return raw if isinstance(raw, dict) else {}


def parse_operation(data: dict) -> dict:
    payer = _party(data, "payer")
    receiver = _party(data, "receiver")
    counterparty = _party(data, "counterParty")
    if not counterparty:
        counterparty = _party(data, "counterparty")
    payer_name = _text(_pick(payer, "name")) or _text(_pick(counterparty, "name"))
    return {
        "operation_id": _text(_pick(data, "operationId", "OperationId")),
        "account_number": _text(_pick(data, "accountNumber")),
        "operation_date": _parse_dt(_pick(data, "operationDate", "drawDate")),
        "operation_status": _text(_pick(data, "operationStatus")),
        "type_of_operation": _text(_pick(data, "typeOfOperation")),
        "document_number": _text(_pick(data, "documentNumber")),
        "amount": _money(_pick(data, "operationAmount")),
        "ruble_amount": _money(_pick(data, "rubleAmount")) if _pick(data, "rubleAmount") is not None else None,
        "currency_code": _text(_pick(data, "operationCurrencyDigitalCode")),
        "pay_purpose": _text(_pick(data, "payPurpose")),
        "description": _text(_pick(data, "description")),
        "payer_name": payer_name,
        "payer_inn": _text(_pick(payer, "inn")) or _text(_pick(counterparty, "inn")),
        "payer_account": _text(_pick(payer, "acct")) or _text(_pick(counterparty, "account")),
        "receiver_name": _text(_pick(receiver, "name")),
        "receiver_inn": _text(_pick(receiver, "inn")),
        "receiver_account": _text(_pick(receiver, "acct")),
    }


def _fingerprint(fields: dict) -> str | None:
    document = fields["document_number"]
    when = fields["operation_date"]
    if not document or when is None:
        return None
    purpose = fields["pay_purpose"][:180]
    stamp = when.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M")
    return "|".join((fields["account_number"], document, str(fields["amount"]), stamp, purpose))


def iter_operations(body) -> list[dict]:
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if not isinstance(body, dict):
        return []
    batch = body.get("operations")
    if isinstance(batch, list):
        return [item for item in batch if isinstance(item, dict)]
    nested = body.get("operation") or body.get("Operation")
    if isinstance(nested, dict):
        return [nested]
    if _pick(body, "operationId", "OperationId"):
        return [body]
    return []


def client_ip(request) -> str:
    forwarded = _text(request.META.get("HTTP_X_FORWARDED_FOR"))
    if forwarded:
        return forwarded.split(",")[0].strip()
    return _text(request.META.get("REMOTE_ADDR"))


def webhook_authorized(request) -> tuple[bool, int]:
    expected = (getattr(settings, "TBANK_WEBHOOK_TOKEN", "") or "").strip()
    if not expected:
        return False, 503
    header = _text(request.META.get("HTTP_AUTHORIZATION"))
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token.strip(), expected):
        return False, 401
    if client_ip(request) not in WEBHOOK_IPS:
        return False, 403
    return True, 200


def our_account() -> str:
    return (getattr(settings, "TBANK_ACCOUNT_NUMBER", "") or "").strip()


def is_incoming_to_us(fields: dict) -> bool:
    if fields["type_of_operation"].lower() != "credit":
        return False
    account = our_account()
    if not account:
        return True
    seen = {fields["account_number"], fields["receiver_account"]}
    seen.discard("")
    if not seen:
        return True
    return account in seen


def expected_rub(order) -> Decimal | None:
    try:
        return convert_krw_amount(order.amount_krw or 0, "RUB")
    except (ValueError, InvalidOperation):
        return None


def format_rub(amount: Decimal | None) -> str:
    if amount is None:
        return ""
    quantized = amount.quantize(Decimal("0.01"))
    if quantized == quantized.to_integral_value():
        text = f"{int(quantized):,}".replace(",", " ")
    else:
        text = f"{quantized:,.2f}".replace(",", " ").replace(".", ",")
    return f"{text} ₽"


def amounts_close(paid: Decimal, expected: Decimal) -> bool:
    if expected <= 0:
        return False
    diff = abs(paid - expected)
    return diff <= Decimal("1.00") or diff / expected <= Decimal("0.01")


def _name_tokens(value: str) -> set[str]:
    return {part for part in _TOKEN_RE.split(value.lower()) if len(part) >= 3}


def names_match(payer: str, client: str) -> bool:
    left = _name_tokens(payer)
    right = _name_tokens(client)
    if not left or not right:
        return False
    return bool(left & right)


def order_ids_in_text(*parts: str) -> list[str]:
    found = []
    for part in parts:
        upper = _text(part).upper()
        for match in _ID_RE.findall(upper):
            if match not in found:
                found.append(match)
    return found


def _paid_amount(fields: dict) -> Decimal:
    if fields["currency_code"] and fields["currency_code"] != "643" and fields["ruble_amount"]:
        return fields["ruble_amount"]
    return fields["amount"]


def identify(fields: dict):
    """Вернуть (заказ, статус сверки, комментарий)."""
    if not is_incoming_to_us(fields):
        return None, TBankOperation.Match.UNMATCHED, ""
    status = (fields["operation_status"] or "").lower()
    if status and status != "transaction":
        return None, TBankOperation.Match.UNMATCHED, "ещё не подтверждена банком"

    paid = _paid_amount(fields)
    ids = order_ids_in_text(fields["pay_purpose"], fields["description"])
    payer = fields["payer_name"]

    if ids:
        order = SiteOrder.objects.filter(public_id=ids[0]).first()
        if order is None:
            return None, TBankOperation.Match.UNMATCHED, f"в назначении {ids[0]}, заказа нет"
        quote = expected_rub(order)
        name_ok = names_match(payer, order.first_name)
        name_note = _name_note(payer, name_ok)
        if quote is None:
            return order, TBankOperation.Match.AMOUNT_UNKNOWN, name_note
        if amounts_close(paid, quote):
            if payer and name_ok:
                return order, TBankOperation.Match.MATCHED, name_note
            return order, TBankOperation.Match.NAME_DIFFERS, name_note
        return (
            order,
            TBankOperation.Match.AMOUNT_DIFFERS,
            f"в выписке {format_rub(paid)}, по заказу {format_rub(quote)}. {name_note}".strip(),
        )

    since = timezone.now() - timedelta(days=45)
    candidates = []
    orders = SiteOrder.objects.filter(status__in=OPEN_STATUSES, created_at__gte=since)
    for order in orders:
        quote = expected_rub(order)
        if quote is None or not amounts_close(paid, quote):
            continue
        if names_match(payer, order.first_name):
            candidates.append(order)
    if len(candidates) == 1:
        return candidates[0], TBankOperation.Match.BY_PAYER, "номер заказа в назначении не найден"
    return None, TBankOperation.Match.UNMATCHED, ""


def _name_note(payer: str, name_ok: bool) -> str:
    if not payer:
        return "имя плательщика не указано"
    if name_ok:
        return "плательщик совпал"
    return "имя плательщика не совпало с заказом"


def _fill(current, new):
    if new in (None, ""):
        return current
    return new


def save_operation(payload: dict, *, source: str) -> TBankOperation | None:
    fields = parse_operation(payload)
    if not fields["operation_id"]:
        logger.warning("T-Bank: операция без operationId, источник %s", source)
        return None
    fingerprint = _fingerprint(fields)
    row = TBankOperation.objects.filter(operation_id=fields["operation_id"]).first()
    if row is None:
        row = TBankOperation.objects.filter(statement_operation_id=fields["operation_id"]).first()
    if row is None and fingerprint:
        row = TBankOperation.objects.filter(fingerprint=fingerprint).first()

    if row is None:
        row = TBankOperation(operation_id=fields["operation_id"], source=source)
    elif row.operation_id != fields["operation_id"] and not row.statement_operation_id:
        row.statement_operation_id = fields["operation_id"]

    for key in (
        "account_number",
        "operation_status",
        "type_of_operation",
        "document_number",
        "currency_code",
        "pay_purpose",
        "description",
        "payer_name",
        "payer_inn",
        "payer_account",
        "receiver_name",
        "receiver_inn",
        "receiver_account",
    ):
        setattr(row, key, _fill(getattr(row, key), fields[key]))
    if fields["operation_date"] is not None:
        row.operation_date = fields["operation_date"]
    if fields["amount"]:
        row.amount = fields["amount"]
    if fields["ruble_amount"] is not None:
        row.ruble_amount = fields["ruble_amount"]
    if fingerprint and row.fingerprint != fingerprint:
        taken = TBankOperation.objects.filter(fingerprint=fingerprint)
        if row.pk:
            taken = taken.exclude(pk=row.pk)
        if not taken.exists():
            row.fingerprint = fingerprint
    if not row.source:
        row.source = source
    row.raw = payload if isinstance(payload, dict) else {}
    apply_match(row, fields)
    row.save()
    return row


def apply_match(row: TBankOperation, fields: dict | None = None) -> None:
    if fields is None:
        fields = {
            "account_number": row.account_number,
            "receiver_account": row.receiver_account,
            "type_of_operation": row.type_of_operation,
            "operation_status": row.operation_status,
            "pay_purpose": row.pay_purpose,
            "description": row.description,
            "payer_name": row.payer_name,
            "amount": row.amount,
            "ruble_amount": row.ruble_amount,
            "currency_code": row.currency_code,
        }
    order, status, note = identify(fields)
    row.order = order
    row.match_status = status
    row.match_note = note[:255]


def rematch_recent() -> int:
    since = timezone.now() - timedelta(days=45)
    rows = TBankOperation.objects.filter(
        order__isnull=True,
        type_of_operation__iexact="Credit",
        operation_date__gte=since,
    ).order_by("-operation_date")[:100]
    count = 0
    for row in rows:
        apply_match(row)
        if row.order_id:
            row.save(update_fields=["order", "match_status", "match_note", "updated_at"])
            count += 1
    return count


def payment_instructions(order) -> str:
    quote = expected_rub(order)
    lines = [
        f"Оплата заказа {order.public_id}",
        f"Сумма: {format_rub(quote)}" if quote is not None else "Сумма: курс KRW/RUB не задан",
        f"Назначение платежа: Оплата заказа {order.public_id}",
        "",
        "Получатель",
    ]
    pairs = (
        ("Наименование", getattr(settings, "TBANK_PAYEE_NAME", "")),
        ("ИНН", getattr(settings, "TBANK_INN", "")),
        ("КПП", getattr(settings, "TBANK_KPP", "")),
        ("Р/с", our_account()),
        ("Банк", getattr(settings, "TBANK_BANK", "")),
        ("БИК", getattr(settings, "TBANK_BIK", "")),
        ("К/с", getattr(settings, "TBANK_CORR_ACCOUNT", "")),
    )
    filled = [f"{label}: {value}" for label, value in pairs if _text(value)]
    if filled:
        lines.extend(filled)
    else:
        lines.append("Реквизиты Т-Банка в .env не заданы")
    return "\n".join(lines)


def order_payment_panel(order) -> dict:
    rematch_recent()
    quote = expected_rub(order)
    operations = []
    for row in order.tbank_operations.all():
        operations.append(
            {
                "when": timezone.localtime(row.operation_date).strftime("%d.%m.%Y %H:%M")
                if row.operation_date
                else "",
                "amount": format_rub(row.amount),
                "payer": row.payer_name,
                "purpose": row.pay_purpose,
                "status_label": row.get_match_status_display() or "Без сверки",
                "note": row.match_note,
                "confirmed": row.match_status == TBankOperation.Match.MATCHED,
            }
        )
    return {
        "instructions": payment_instructions(order),
        "expected_rub": format_rub(quote),
        "operations": operations,
        "can_mark": order.status in (*OPEN_STATUSES, SiteOrder.Status.FAILED),
        "configured": bool((getattr(settings, "TBANK_TOKEN", "") or "").strip() and our_account()),
    }


def confirm_order_payment(order) -> str:
    if order.status == SiteOrder.Status.PAID:
        return "Заказ уже оплачен"
    if order.status == SiteOrder.Status.CANCELLED:
        return "Отменённый заказ нельзя отметить оплаченным"
    order.status = SiteOrder.Status.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at", "updated_at"])
    row = (
        order.tbank_operations.filter(match_status=TBankOperation.Match.MATCHED).order_by("-operation_date").first()
        or order.tbank_operations.order_by("-operation_date").first()
    )
    if row and row.match_status == TBankOperation.Match.MATCHED:
        return f"Оплата отмечена. В выписке {row.amount} ₽ от {row.payer_name or 'плательщика'}."
    if row:
        detail = row.match_note or row.get_match_status_display()
        return f"Оплата отмечена. В выписке есть операция, её нужно сверить: {detail}"
    return "Оплата отмечена. В выписке Т-Банка подходящий платёж не найден."


def fetch_statement(*, account: str, token: str, start, end) -> list[dict]:
    url = (getattr(settings, "TBANK_API_BASE", "") or "https://business.tbank.ru/openapi").rstrip("/") + STATEMENT_PATH
    operations = []
    cursor = ""
    for _ in range(20):
        params = {
            "accountNumber": account,
            "from": start.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "operationStatus": "Transaction",
            "limit": 1000,
        }
        if end is not None:
            params["to"] = end.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if cursor:
            params["cursor"] = cursor
        try:
            response = requests.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise TBankError("Т-Банк не ответил") from exc
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code != 200:
            message = ""
            if isinstance(payload, dict):
                message = _text(payload.get("errorMessage"))
            raise TBankError(f"Т-Банк ответил {response.status_code}" + (f": {message}" if message else ""))
        batch = payload.get("operations") if isinstance(payload, dict) else None
        if isinstance(batch, list):
            operations.extend(item for item in batch if isinstance(item, dict))
        cursor = _text(payload.get("nextCursor")) if isinstance(payload, dict) else ""
        if not cursor:
            break
    return operations


def pull_recent_statement(days: int = 14) -> int:
    token = (getattr(settings, "TBANK_TOKEN", "") or "").strip()
    account = our_account()
    if not token or not account:
        raise TBankError("Не заданы TBANK_TOKEN или TBANK_ACCOUNT_NUMBER")
    end = timezone.now() + timedelta(minutes=5)
    start = end - timedelta(days=max(days, 1))
    payloads = fetch_statement(account=account, token=token, start=start, end=end)
    saved = 0
    for payload in payloads:
        if save_operation(payload, source="statement"):
            saved += 1
    return saved
