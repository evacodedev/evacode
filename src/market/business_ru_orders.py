from decimal import Decimal, ROUND_HALF_UP
import re

import requests
from django.conf import settings

from .paypal import receipt_url
from .utils import BusinessRuAPIClient


class BusinessRuOrderError(Exception):
    pass


def _result_id(payload):
    result = payload.get("result") if isinstance(payload, dict) else payload
    if isinstance(result, dict):
        return result.get("id") or result.get("ID")
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict):
            return first.get("id")
        return first
    return result


class BusinessRuOrderClient(BusinessRuAPIClient):
    def request(self, method: str, model: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        params["app_id"] = self.app_id
        hashed = self.get_hash(params=params, token=self.token)
        url = f"{self.base_url}/{model}.json"
        body = {**params, "app_psw": hashed}
        method_l = method.lower()
        if method_l == "get":
            response = requests.get(url, params=body, timeout=30)
        elif method_l == "put":
            response = requests.put(url, data=body, timeout=30)
        elif method_l == "delete":
            response = requests.delete(url, data=body, timeout=30)
        else:
            response = requests.post(url, data=body, timeout=30)
        try:
            data = response.json()
        except ValueError as exc:
            raise BusinessRuOrderError(f"{model} {method}: не JSON ({response.status_code}) {response.text}") from exc
        if not response.ok:
            raise BusinessRuOrderError(f"{model} {method}: HTTP {response.status_code} {data}")
        if isinstance(data, dict) and data.get("status") == "error":
            raise BusinessRuOrderError(
                f"{model} {method}: {data.get('error_text') or data.get('error_code') or data}"
            )
        return data

    def find_by_name(self, model: str, name: str, name_field: str = "name"):
        wanted = (name or "").strip().lower()
        if not wanted:
            return None
        payload = self.request("get", model)
        for item in payload.get("result") or []:
            if str(item.get(name_field, "")).strip().lower() == wanted:
                return item
        return None


def _contact_type_id(client: BusinessRuOrderClient, needle: str):
    payload = client.request("get", "contactinfotypes")
    needle = needle.lower()
    for item in payload.get("result") or []:
        name = str(item.get("name") or "").lower()
        if needle in name:
            return item.get("id")
    return None


def _find_partner(client: BusinessRuOrderClient, email: str, phone_digits: str):
    if email:
        payload = client.request("get", "partners", {"email": email})
        result = payload.get("result") or []
        if result:
            return result[0]
    if phone_digits:
        payload = client.request("get", "partners", {"phone": phone_digits})
        result = payload.get("result") or []
        if result:
            return result[0]
    return None


def _extract_field_names(payload) -> list[str]:
    result = payload.get("result") if isinstance(payload, dict) else payload
    if isinstance(result, dict):
        params = result.get("params")
        if isinstance(params, dict) and params:
            return [str(key) for key in params.keys()]
        fields = result.get("fields") or result.get("attributes") or result.get("columns") or []
        if not fields:
            return [str(key) for key in result.keys()]
        result = fields
    if isinstance(result, list) and result and isinstance(result[0], dict):
        sample = result[0]
        if "id" in sample and not any(key in sample for key in ("type", "required", "readonly")):
            return [str(key) for key in sample.keys()]
        names = []
        for item in result:
            if isinstance(item, dict):
                name = item.get("name") or item.get("field")
                if name:
                    names.append(str(name))
            elif isinstance(item, str):
                names.append(item)
        return names
    return []


def _model_field_names(client: BusinessRuOrderClient, model: str) -> list[str]:
    for params in ({"help": "1"}, {}):
        try:
            names = _extract_field_names(client.request("get", model, params))
        except BusinessRuOrderError:
            continue
        if names:
            return names
    return []


def _pick_field(names: list[str], *candidates: str) -> str | None:
    lookup = {name.lower(): name for name in names}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _get_by_id(client: BusinessRuOrderClient, model: str, record_id):
    payload = client.request("get", model, {"id": record_id})
    result = payload.get("result") if isinstance(payload, dict) else payload
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict) and str(item.get("id")) == str(record_id):
                return item
        return result[0] if len(result) == 1 and isinstance(result[0], dict) else None
    if isinstance(result, dict):
        return result
    return None


def _current_account_id(client: BusinessRuOrderClient, org_id: str):
    payload = client.request("get", "currentaccounts")
    accounts = payload.get("result") or []
    org_accounts = [
        acc for acc in accounts if not org_id or str(acc.get("organization_id") or "") in ("", str(org_id))
    ] or accounts
    configured = str(getattr(settings, "BUSINESS_RU_CURRENT_ACCOUNT_ID", "") or "").strip()
    if configured:
        for acc in org_accounts:
            if str(acc.get("id")) == configured:
                return str(acc.get("id"))
        return configured
    for acc in org_accounts:
        name = str(acc.get("name") or "").lower()
        if "paypal" in name:
            return str(acc.get("id"))
    names = ", ".join(f"{acc.get('id')} {acc.get('name')}" for acc in org_accounts) or "список пуст"
    raise BusinessRuOrderError(
        "Не найден расчётный счёт PayPal. Укажите BUSINESS_RU_CURRENT_ACCOUNT_ID. "
        f"Доступные счета: {names}"
    )


def _payment_account_params(client: BusinessRuOrderClient, account_id: str) -> dict:
    names = _model_field_names(client, "paymentin")
    field = _pick_field(
        names,
        "current_account_id",
        "currentaccount_id",
        "organization_currentaccount_id",
        "organizationcurrentaccount_id",
    )
    if field:
        return {field: account_id}
    return {"current_account_id": account_id}


def _payment_operation_id(client: BusinessRuOrderClient):
    configured = str(getattr(settings, "BUSINESS_RU_PAYMENT_OPERATION_ID", "") or "").strip()
    if configured:
        return configured
    wanted = str(getattr(settings, "BUSINESS_RU_PAYMENT_OPERATION_NAME", "") or "").strip().lower()
    payload = client.request("get", "paymentinoperations")
    operations = payload.get("result") or []
    if wanted:
        for item in operations:
            if str(item.get("name") or "").strip().lower() == wanted:
                return item.get("id")
    for item in operations:
        name = str(item.get("name") or "").lower()
        if "покупател" in name and "оплат" in name:
            return item.get("id")
    for item in operations:
        name = str(item.get("name") or "").lower()
        if "оплат" in name:
            return item.get("id")
    if operations:
        return operations[0].get("id")
    return None


def _as_money(value) -> Decimal:
    try:
        amount = Decimal(str(value).replace(",", ".").strip())
    except Exception:
        return Decimal("0")
    return amount if amount > 0 else Decimal("0")


def _money_str(value) -> str:
    return str(_as_money(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _record_sum(record: dict | None) -> Decimal:
    if not isinstance(record, dict):
        return Decimal("0")
    for key in ("sum", "total", "amount"):
        amount = _as_money(record.get(key))
        if amount:
            return amount
    return Decimal("0")


def _payment_sum_krw(order) -> Decimal:
    krw = _as_money(order.amount_krw)
    if krw:
        return krw
    return _as_money(order.amount_usd)


def _account_record(client: BusinessRuOrderClient, account_id: str) -> dict:
    payload = client.request("get", "currentaccounts")
    for acc in payload.get("result") or []:
        if str(acc.get("id")) == str(account_id):
            return acc
    return {}


def _ensure_order_goods_krw(client: BusinessRuOrderClient, order) -> None:
    if not order.business_ru_order_id:
        return
    try:
        payload = client.request(
            "get", "customerordergoods", {"customer_order_id": order.business_ru_order_id}
        )
    except BusinessRuOrderError:
        return
    items = list(order.items.all())
    for line in payload.get("result") or []:
        if not isinstance(line, dict) or not line.get("id"):
            continue
        good_id = str(line.get("good_id") or "")
        item = next((row for row in items if str(row.good_id_snapshot) == good_id), None)
        if item is None:
            continue
        if _as_money(line.get("price")) == _as_money(item.price_krw):
            continue
        client.request(
            "put",
            "customerordergoods",
            {"id": line["id"], "price": item.price_krw, "amount": item.quantity},
        )


def _paypal_rate_text(order) -> str:
    rate = order.usd_rate_snapshot
    if not rate:
        return ""
    pretty = Decimal(str(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f" Курс 1 USD = {pretty} ₩."


def _payment_comment(order) -> str:
    receipt = order.paypal_receipt_url or receipt_url(order.paypal_capture_id)
    return (
        f"PayPal списал {order.amount_usd} USD.{_paypal_rate_text(order)} "
        f"В учёте {order.amount_krw} ₩. "
        f"Заказ сайта {order.public_id}. "
        f"Order ID {order.paypal_order_id}. Capture {order.paypal_capture_id}. "
        f"{order.email} {order.phone}. Чек: {receipt}"
    )[:2000]


def _customer_order_comment(order) -> str:
    return (
        f"Оплачено PayPal: {order.amount_usd} USD ({order.amount_krw} ₩)."
        f"{_paypal_rate_text(order)} "
        f"Заказ сайта {order.public_id}. "
        f"PayPal {order.paypal_order_id} / {order.paypal_capture_id}. "
        f"{order.email} {order.phone}. {order.comment}"
    )[:2000]


def _payment_is_linked(client: BusinessRuOrderClient, payment_id, order_id) -> bool:
    try:
        payload = client.request("get", "paymentintodocument", {"paymentin_id": payment_id})
    except BusinessRuOrderError:
        return False
    for item in payload.get("result") or []:
        if not isinstance(item, dict):
            continue
        linked = item.get("document_id") or item.get("customer_order_id") or item.get("object_id")
        if str(linked) == str(order_id):
            return True
    return False


_EXCEED_SUM_RE = re.compile(r"Сумма привязываемого документа\s*[-—]\s*([0-9]+(?:[.,][0-9]+)?)", re.I)


def _set_payment_sum(client: BusinessRuOrderClient, payment_id, amount: Decimal) -> None:
    wanted = _as_money(_money_str(amount))
    current = _record_sum(_get_by_id(client, "paymentin", payment_id))
    if current == wanted:
        return
    client.request("put", "paymentin", {"id": payment_id, "sum": _money_str(wanted)})


def _link_payment_to_order(client: BusinessRuOrderClient, payment_id, order) -> None:
    order_id = order.business_ru_order_id
    if _payment_is_linked(client, payment_id, order_id):
        return
    amount = _payment_sum_krw(order)
    last_error = None
    tried = set()
    for _ in range(3):
        key = _money_str(amount)
        if key in tried:
            break
        tried.add(key)
        try:
            client.request(
                "post",
                "paymentintodocument",
                {
                    "paymentin_id": payment_id,
                    "customer_order_id": order_id,
                    "sum": key,
                },
            )
            return
        except BusinessRuOrderError as exc:
            last_error = exc
            match = _EXCEED_SUM_RE.search(str(exc))
            if not match:
                raise
            amount = _as_money(match.group(1))
            if not amount:
                raise
    if last_error:
        raise last_error


def _ensure_payment_account(client: BusinessRuOrderClient, payment_id, account_id: str) -> None:
    record = _get_by_id(client, "paymentin", payment_id) or {}
    current = str(
        record.get("current_account_id")
        or record.get("currentaccount_id")
        or record.get("organization_currentaccount_id")
        or ""
    )
    if current == str(account_id):
        return
    params = {"id": payment_id, **_payment_account_params(client, account_id)}
    client.request("put", "paymentin", params)


def _export_payment(client: BusinessRuOrderClient, order, partner_id, org_id: str, employee_id: str) -> None:
    account_id = _current_account_id(client, org_id)
    operation_id = _payment_operation_id(client)
    if not operation_id:
        raise BusinessRuOrderError(
            "Не найден вид операции входящего платежа. Укажите BUSINESS_RU_PAYMENT_OPERATION_ID"
        )
    payment_id = str(order.business_ru_payment_id or "").strip()
    payment_sum = _payment_sum_krw(order)
    account = _account_record(client, account_id)
    payment_params = {
        "partner_id": partner_id,
        "organization_id": org_id,
        "author_employee_id": employee_id,
        "responsible_employee_id": employee_id,
        "operation_id": operation_id,
        "sum": _money_str(payment_sum),
        "held": 1,
        "comment": _payment_comment(order),
        **_payment_account_params(client, account_id),
    }
    if account.get("currency_id"):
        payment_params["currency_id"] = account["currency_id"]
    if not payment_id:
        try:
            created = client.request("post", "paymentin", payment_params)
        except BusinessRuOrderError:
            payment_params.pop("currency_id", None)
            created = client.request("post", "paymentin", payment_params)
        payment_id = str(_result_id(created) or "")
        if not payment_id:
            raise BusinessRuOrderError(f"Не удалось создать входящий платёж: {created}")
        order.business_ru_payment_id = payment_id
        order.save(update_fields=["business_ru_payment_id", "updated_at"])
    else:
        _set_payment_sum(client, payment_id, payment_sum)
        actual = _record_sum(_get_by_id(client, "paymentin", payment_id))
        if actual != _as_money(_money_str(payment_sum)):
            created = client.request("post", "paymentin", payment_params)
            payment_id = str(_result_id(created) or "")
            if not payment_id:
                raise BusinessRuOrderError(f"Не удалось создать входящий платёж: {created}")
            order.business_ru_payment_id = payment_id
            order.save(update_fields=["business_ru_payment_id", "updated_at"])
    _ensure_payment_account(client, payment_id, account_id)
    _link_payment_to_order(client, payment_id, order)


def export_paid_order(order) -> None:
    org_id = str(settings.BUSINESS_RU_ORGANIZATION_ID or "").strip()
    employee_id = str(settings.BUSINESS_RU_EMPLOYEE_ID or "").strip()
    if not org_id or not employee_id:
        raise BusinessRuOrderError(
            "Не заданы BUSINESS_RU_ORGANIZATION_ID / BUSINESS_RU_EMPLOYEE_ID — заказ сохранён локально"
        )

    client = BusinessRuOrderClient()
    store = None
    status = None
    if not order.business_ru_order_id:
        store = client.find_by_name("stores", settings.BUSINESS_RU_STORE_NAME)
        status = client.find_by_name("customerorderstatus", settings.BUSINESS_RU_STATUS_NAME)
        if status is None:
            payload = client.request("get", "customerorderstatus")
            for item in payload.get("result") or []:
                if item.get("default"):
                    status = item
                    break
        if store is None:
            raise BusinessRuOrderError(f"Склад «{settings.BUSINESS_RU_STORE_NAME}» не найден")
        if status is None:
            raise BusinessRuOrderError(f"Статус «{settings.BUSINESS_RU_STATUS_NAME}» не найден")

    partner = _find_partner(client, order.email, order.phone_digits)
    if partner:
        partner_id = partner.get("id")
    else:
        created = client.request(
            "post",
            "partners",
            {
                "name": order.first_name,
                "customer": 1,
                "note": f"Сайт evacode.org, {order.email}, {order.phone}",
            },
        )
        partner_id = _result_id(created)
        if not partner_id:
            raise BusinessRuOrderError(f"Не удалось создать контрагента: {created}")
        email_type = _contact_type_id(client, "mail") or _contact_type_id(client, "email")
        phone_type = _contact_type_id(client, "телефон") or _contact_type_id(client, "phone")
        if email_type:
            client.request(
                "post",
                "partnercontactinfo",
                {
                    "partner_id": partner_id,
                    "contact_info_type_id": email_type,
                    "contact_info": order.email,
                },
            )
        if phone_type:
            client.request(
                "post",
                "partnercontactinfo",
                {
                    "partner_id": partner_id,
                    "contact_info_type_id": phone_type,
                    "contact_info": order.phone,
                    "phone": order.phone_digits,
                },
            )

    if not order.business_ru_order_id:
        delivery_address = ", ".join(
            part for part in [order.postal_code, order.country, order.city, order.address] if part
        )
        comment = _customer_order_comment(order)
        order_params = {
            "partner_id": partner_id,
            "organization_id": org_id,
            "author_employee_id": employee_id,
            "responsible_employee_id": employee_id,
            "status_id": status["id"],
            "comment": comment[:2000],
            "delivery_address": delivery_address[:500],
        }
        created_order = client.request("post", "customerorders", order_params)
        business_order_id = _result_id(created_order)
        if not business_order_id:
            raise BusinessRuOrderError(f"Не удалось создать заказ покупателя: {created_order}")

        for item in order.items.all():
            client.request(
                "post",
                "customerordergoods",
                {
                    "customer_order_id": business_order_id,
                    "good_id": item.good_id_snapshot,
                    "amount": item.quantity,
                    "price": item.price_krw,
                    "store_id": store["id"],
                },
            )

        order.business_ru_partner_id = str(partner_id)
        order.business_ru_order_id = str(business_order_id)
        order.business_ru_error = ""
        order.save(update_fields=["business_ru_partner_id", "business_ru_order_id", "business_ru_error", "updated_at"])
    else:
        _ensure_order_goods_krw(client, order)

    try:
        _export_payment(client, order, partner_id, org_id, employee_id)
        if (order.business_ru_error or "").startswith("Заказ создан, оплата не выгружена"):
            order.business_ru_error = ""
            order.save(update_fields=["business_ru_error", "updated_at"])
    except Exception as exc:
        order.business_ru_error = f"Заказ создан, оплата не выгружена: {exc}"[:4000]
        order.save(update_fields=["business_ru_error", "updated_at"])
        raise BusinessRuOrderError(order.business_ru_error)
