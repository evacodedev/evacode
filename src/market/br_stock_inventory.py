from contextlib import contextmanager
from datetime import datetime, timedelta
import os

import requests
from django.conf import settings
from django.db import connection
from django.utils import timezone

from .business_ru_orders import (
    BusinessRuOrderClient,
    BusinessRuOrderError,
    _document_number,
    _result_id,
)
from .utils import load_evacode_env


TEST_STORE_ID = "2787290"
KZT_CURRENCY_ID = "7"
KZ_PURCHASE_PRICE_TYPE_ID = "936485"
KZ_SALE_PRICE_TYPES = (
    ("price_wholesale_small", "BUSINESS_RU_KZ_PRICE_TYPE_WHOLESALE_SMALL", "1058601"),
    ("price_wholesale_medium", "BUSINESS_RU_KZ_PRICE_TYPE_WHOLESALE_MEDIUM", "1709914"),
    ("price_wholesale_large", "BUSINESS_RU_KZ_PRICE_TYPE_WHOLESALE_LARGE", "1058605"),
    ("price_retail", "BUSINESS_RU_KZ_PRICE_TYPE_RETAIL", "936503"),
)
KZ_SYNC_LOCK_KEY = 87236402
KZ_SYNC_INTERVAL_MIN_HOURS = 1
KZ_SYNC_INTERVAL_MAX_HOURS = 168


class BrStockInventoryError(BusinessRuOrderError):
    pass


def _qty(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def parse_crm_catalog(payload) -> tuple[dict[int, float], dict[int, dict[str, float]]]:
    if isinstance(payload, dict):
        products = payload.get("products")
    else:
        products = payload
    quantities = {}
    prices = {}
    fields = tuple(item[0] for item in KZ_SALE_PRICE_TYPES)
    for item in products or []:
        if not isinstance(item, dict):
            continue
        try:
            good_id = int(item.get("external_id"))
        except (TypeError, ValueError):
            continue
        quantities[good_id] = _qty(item.get("quantity"))
        row = {}
        for field in fields:
            if item.get(field) in (None, ""):
                continue
            amount = _qty(item.get(field))
            if amount > 0:
                row[field] = amount
        if row:
            prices[good_id] = row
    return quantities, prices


def parse_crm_products(payload) -> dict[int, float]:
    quantities, _ = parse_crm_catalog(payload)
    return quantities


def store_total(remains, store_id) -> float | None:
    wanted = str(store_id)
    found = False
    total = 0.0
    for item in remains or []:
        store = item.get("store") if isinstance(item, dict) else None
        if not isinstance(store, dict) or str(store.get("id")) != wanted:
            continue
        found = True
        amount = item.get("amount") if isinstance(item.get("amount"), dict) else {}
        total = _qty(amount.get("total"))
    return total if found else None


def merge_inventory_rows(current_by_id: dict[int, float], api_by_id: dict[int, float]) -> list[dict]:
    rows = []
    for good_id in sorted(set(current_by_id) | set(api_by_id)):
        amount_curr = _qty(current_by_id.get(good_id, 0))
        amount_fact = _qty(api_by_id.get(good_id, 0))
        if amount_curr == 0 and amount_fact == 0:
            continue
        rows.append(
            {
                "good_id": good_id,
                "amount_curr": amount_curr,
                "amount_fact": amount_fact,
            }
        )
    return rows


def surplus_rows(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        delta = _qty(row.get("amount_fact")) - _qty(row.get("amount_curr"))
        if delta <= 0:
            continue
        result.append({"good_id": row["good_id"], "amount": delta})
    return result


def shortage_rows(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        delta = _qty(row.get("amount_curr")) - _qty(row.get("amount_fact"))
        if delta <= 0:
            continue
        result.append({"good_id": row["good_id"], "amount": delta})
    return result


def _good_cost(good: dict) -> float:
    return pick_kz_purchase_price(good)


def pick_kz_purchase_price(good: dict) -> float:
    chosen = 0.0
    for item in good.get("prices") or []:
        if not isinstance(item, dict):
            continue
        price_type = item.get("price_type") if isinstance(item.get("price_type"), dict) else {}
        currency = price_type.get("currency") if isinstance(price_type.get("currency"), dict) else {}
        currency_id = str(currency.get("id") or price_type.get("currency_id") or "")
        name = " ".join((price_type.get("name") or "").lower().replace("ё", "е").split())
        if currency_id != KZT_CURRENCY_ID:
            continue
        if "закуп" in name:
            chosen = _qty(item.get("price"))
    return chosen


def _is_held(record: dict) -> bool:
    held = record.get("held")
    return held in (True, 1, "1", "true", "True")


def hold_document(client: BusinessRuOrderClient, model: str, record_id) -> None:
    if not record_id:
        return
    client.request("put", model, {"id": record_id, "held": 1})


def hold_stock_documents(client: BusinessRuOrderClient, summary: dict) -> dict:
    summary.setdefault("held_errors", [])
    for id_key, model, held_key in (
        ("posting_id", "postings", "posting_held"),
        ("charge_id", "charges", "charge_held"),
        ("inventory_id", "inventories", "inventory_held"),
    ):
        record_id = summary.get(id_key)
        summary[held_key] = False
        if not record_id:
            continue
        try:
            hold_document(client, model, record_id)
            summary[held_key] = True
        except BusinessRuOrderError as extra:
            summary["held_errors"].append(f"{model} {record_id}: {extra}")
    return summary


def _parse_br_datetime(value) -> datetime | None:
    text = str(value or "").strip().replace(" MSK", "").replace(" UTC", "")
    if not text:
        return None
    if len(text) >= 19:
        text = text[:19]
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def fetch_kz_purchase_prices(client: BusinessRuOrderClient, price_type_id: str) -> dict[int, float]:
    costs = {}
    if not str(price_type_id or "").strip():
        return costs
    page = 1
    while True:
        payload = client.request(
            "get",
            "currentprices",
            {"price_type_id": price_type_id, "page": page},
        )
        rows = payload.get("result") or []
        if not isinstance(rows, list) or not rows:
            break
        for item in rows:
            if not isinstance(item, dict):
                continue
            try:
                good_id = int(item.get("good_id"))
            except (TypeError, ValueError):
                continue
            price = _qty(item.get("price"))
            if price:
                costs[good_id] = price
        if len(rows) < 250:
            break
        page += 1
    return costs


def fetch_crm_catalog(url: str, token: str) -> tuple[dict[int, float], dict[int, dict[str, float]]]:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise BrStockInventoryError(
            f"CRM stock: не JSON ({response.status_code}) {response.text[:500]}"
        ) from exc
    if not response.ok:
        raise BrStockInventoryError(f"CRM stock: HTTP {response.status_code} {payload}")
    return parse_crm_catalog(payload)


def fetch_crm_stock(url: str, token: str) -> dict[int, float]:
    quantities, _ = fetch_crm_catalog(url, token)
    return quantities


def fetch_store_snapshot(client: BusinessRuOrderClient, store_id) -> tuple[dict[int, float], dict[int, float]]:
    totals = {}
    costs = {}
    page = 1
    while True:
        payload = client.request(
            "get",
            "goods",
            {
                "page": page,
                "with_remains": 1,
                "with_prices": 1,
                "with_attributes": 0,
                "archive": 0,
                "filter_positive_remains": 0,
                "filter_positive_free_remains": 0,
            },
        )
        goods = payload.get("result") or []
        if not goods:
            break
        for good in goods:
            if not isinstance(good, dict):
                continue
            try:
                good_id = int(good.get("id"))
            except (TypeError, ValueError):
                continue
            cost = _good_cost(good)
            if cost:
                costs[good_id] = cost
            total = store_total(good.get("remains"), store_id)
            if total is None or total == 0:
                continue
            totals[good_id] = total
        if len(goods) < 250:
            break
        page += 1
    return totals, costs


def _unwrap_record(payload, record_id=None) -> dict | None:
    record = payload.get("result") if isinstance(payload, dict) else payload
    if isinstance(record, list):
        if record_id is not None:
            for item in record:
                if isinstance(item, dict) and str(item.get("id")) == str(record_id):
                    return item
        return record[0] if record and isinstance(record[0], dict) else None
    return record if isinstance(record, dict) else None


def kz_purchase_from_postings(client: BusinessRuOrderClient, good_id: int) -> float:
    try:
        payload = client.request("get", "postinggoods", {"good_id": good_id})
    except BusinessRuOrderError:
        return 0.0
    rows = payload.get("result") or []
    if not isinstance(rows, list):
        return 0.0
    chosen_price = 0.0
    chosen_key = None
    doc_cache = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        price = _qty(item.get("price"))
        if not price:
            continue
        posting_id = item.get("posting_id")
        if not posting_id:
            continue
        if posting_id not in doc_cache:
            try:
                doc = client.request("get", "postings", {"id": posting_id})
            except BusinessRuOrderError:
                doc_cache[posting_id] = {}
            else:
                doc_cache[posting_id] = _unwrap_record(doc, posting_id) or {}
        record = doc_cache[posting_id]
        if str(record.get("currency_id") or "") != KZT_CURRENCY_ID:
            continue
        if not _is_held(record):
            continue
        when = _parse_br_datetime(record.get("date") or record.get("updated") or item.get("updated"))
        key = (when or datetime.min, int(item.get("id") or 0))
        if chosen_key is None or key > chosen_key:
            chosen_key = key
            chosen_price = price
    return chosen_price


def fill_missing_costs(client: BusinessRuOrderClient, good_ids: list[int], costs: dict[int, float]) -> dict[int, float]:
    for good_id in good_ids:
        if _qty(costs.get(good_id)):
            continue
        try:
            payload = client.request("get", "goods", {"id": good_id, "with_prices": 1})
        except BusinessRuOrderError:
            continue
        record = payload.get("result")
        if isinstance(record, list):
            record = next(
                (item for item in record if str(item.get("id")) == str(good_id)),
                record[0] if record else None,
            )
        if isinstance(record, dict):
            cost = pick_kz_purchase_price(record)
            if cost:
                costs[good_id] = cost
                continue
        history_price = kz_purchase_from_postings(client, good_id)
        if history_price:
            costs[good_id] = history_price
    return costs


def _prices_equal(left, right) -> bool:
    return round(_qty(left), 2) == round(_qty(right), 2)


def empty_price_stats() -> dict:
    return {
        "prices_updated": 0,
        "prices_unchanged": 0,
        "prices_failed": 0,
        "prices_goods": 0,
        "prices_list_id": None,
        "prices_list_number": None,
        "skipped_price_ids": [],
    }


def collect_kz_sale_price_changes(
    current_by_type: dict[str, dict[int, float]],
    crm_prices: dict[int, dict[str, float]],
    type_ids: dict[str, str],
) -> tuple[dict[int, list[tuple[str, float]]], dict]:
    stats = empty_price_stats()
    changes: dict[int, list[tuple[str, float]]] = {}
    for good_id, row in crm_prices.items():
        items: list[tuple[str, float]] = []
        changed = False
        for field, _env_name, _default in KZ_SALE_PRICE_TYPES:
            type_id = str(type_ids.get(field) or "").strip()
            if not type_id:
                continue
            current = current_by_type.get(type_id, {}).get(good_id)
            crm_val = row.get(field)
            if crm_val not in (None, "") and _qty(crm_val) > 0:
                new_price = _qty(crm_val)
                if current is not None and _prices_equal(current, new_price):
                    stats["prices_unchanged"] += 1
                else:
                    changed = True
                    stats["prices_updated"] += 1
                items.append((type_id, new_price))
            elif current is not None:
                items.append((type_id, _qty(current)))
        if changed and items:
            changes[good_id] = items
    return changes, stats


def apply_kz_sale_prices(
    client: BusinessRuOrderClient,
    crm_prices: dict[int, dict[str, float]],
    cfg: dict,
    *,
    dry_run: bool = False,
) -> dict:
    type_ids = cfg.get("kz_sale_price_type_ids") or {}
    current_by_type = {
        type_id: fetch_kz_purchase_prices(client, type_id)
        for type_id in dict.fromkeys(type_ids.values())
        if type_id
    }
    changes, stats = collect_kz_sale_price_changes(current_by_type, crm_prices, type_ids)
    stats["prices_goods"] = len(changes)
    if dry_run or not changes:
        return stats

    column_ids = []
    for field, _env_name, default in KZ_SALE_PRICE_TYPES:
        type_id = str(type_ids.get(field) or default or "").strip()
        if type_id:
            column_ids.append(type_id)
    try:
        created = client.request(
            "post",
            "salepricelists",
            {
                "organization_id": cfg["org_id"],
                "responsible_employee_id": cfg["employee_id"],
                "owner_employee_id": cfg["employee_id"],
            },
        )
    except BusinessRuOrderError as extra:
        stats["prices_failed"] = stats["prices_updated"]
        stats["prices_updated"] = 0
        stats["skipped_price_ids"] = [f"salepricelists: {extra}"]
        return stats
    list_id = str(_result_id(created) or "")
    if not list_id:
        stats["prices_failed"] = stats["prices_updated"]
        stats["prices_updated"] = 0
        stats["skipped_price_ids"] = ["salepricelists: нет id"]
        return stats
    stats["prices_list_id"] = list_id
    stats["prices_list_number"] = _document_number(client, "salepricelists", list_id, created)[:32]

    failed = 0
    skipped = []
    try:
        for type_id in column_ids:
            client.request(
                "post",
                "salepricelistspricetypes",
                {"price_list_id": list_id, "price_type_id": type_id},
            )
    except BusinessRuOrderError as extra:
        stats["prices_failed"] = stats["prices_updated"]
        stats["prices_updated"] = 0
        stats["skipped_price_ids"] = [f"salepricelistspricetypes: {extra}"]
        return stats

    for good_id, items in changes.items():
        try:
            line = client.request(
                "post",
                "salepricelistgoods",
                {
                    "price_list_id": list_id,
                    "good_id": good_id,
                    "measure_id": 1,
                },
            )
            line_id = str(_result_id(line) or "")
            if not line_id:
                raise BrStockInventoryError("нет id строки назначения")
            for type_id, price in items:
                client.request(
                    "post",
                    "salepricelistgoodprices",
                    {
                        "price_list_good_id": line_id,
                        "price_type_id": type_id,
                        "price": price,
                    },
                )
        except BusinessRuOrderError:
            failed += len(items)
            skipped.append(good_id)
    try:
        client.request("put", "salepricelists", {"id": list_id, "held": 1})
    except BusinessRuOrderError as extra:
        skipped.append(f"проводка назначения {list_id}: {extra}")

    failed_goods = {item for item in skipped if isinstance(item, int)}
    stats["prices_failed"] = failed
    if failed:
        stats["prices_updated"] = 0
    stats["skipped_price_ids"] = skipped[:50]
    stats["prices_goods"] = len({good_id for good_id in changes if good_id not in failed_goods})
    return stats


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def inventory_settings() -> dict:
    load_evacode_env()
    store_id = _env("BUSINESS_RU_INVENTORY_STORE_ID", TEST_STORE_ID)
    org_id = _env("BUSINESS_RU_ORGANIZATION_ID") or str(
        getattr(settings, "BUSINESS_RU_ORGANIZATION_ID", "") or ""
    ).strip()
    employee_id = _env("BUSINESS_RU_EMPLOYEE_ID") or str(
        getattr(settings, "BUSINESS_RU_EMPLOYEE_ID", "") or ""
    ).strip()
    crm_url = _env(
        "CRM_STOCK_URL",
        "https://crm.evacode.kz/api/v1/evacodeorg/stock",
    )
    crm_token = _env("CRM_STOCK_TOKEN")
    currency_id = _env("BUSINESS_RU_INVENTORY_CURRENCY_ID", KZT_CURRENCY_ID)
    warehouse_code = _env("BUSINESS_RU_INVENTORY_WAREHOUSE_CODE", "KZ").upper()
    kz_purchase_price_type_id = _env(
        "BUSINESS_RU_KZ_PURCHASE_PRICE_TYPE_ID",
        KZ_PURCHASE_PRICE_TYPE_ID,
    )
    kz_sale_price_type_ids = {
        field: _env(env_name, default)
        for field, env_name, default in KZ_SALE_PRICE_TYPES
    }
    return {
        "store_id": store_id,
        "warehouse_code": warehouse_code,
        "org_id": org_id,
        "employee_id": employee_id,
        "crm_url": crm_url,
        "crm_token": crm_token,
        "currency_id": currency_id,
        "kz_purchase_price_type_id": kz_purchase_price_type_id,
        "kz_sale_price_type_ids": kz_sale_price_type_ids,
    }


def create_stock_inventory(client: BusinessRuOrderClient | None = None, *, dry_run: bool = False) -> dict:
    cfg = inventory_settings()
    if not cfg["store_id"]:
        raise BrStockInventoryError("Не задан BUSINESS_RU_INVENTORY_STORE_ID")
    if not cfg["org_id"] or not cfg["employee_id"]:
        raise BrStockInventoryError(
            "Не заданы BUSINESS_RU_ORGANIZATION_ID / BUSINESS_RU_EMPLOYEE_ID"
        )
    if not cfg["crm_token"]:
        raise BrStockInventoryError("Не задан CRM_STOCK_TOKEN")

    client = client or BusinessRuOrderClient()
    current, costs = fetch_store_snapshot(client, cfg["store_id"])
    api_qty, api_prices = fetch_crm_catalog(cfg["crm_url"], cfg["crm_token"])
    rows = merge_inventory_rows(current, api_qty)
    costs.update(fetch_kz_purchase_prices(client, cfg["kz_purchase_price_type_id"]))
    fill_missing_costs(client, [row["good_id"] for row in rows], costs)
    summary = {
        "store_id": cfg["store_id"],
        "warehouse_code": cfg["warehouse_code"],
        "current_lines": len(current),
        "api_lines": len(api_qty),
        "inventory_lines": len(rows),
        "surplus": sum(1 for row in rows if row["amount_fact"] > row["amount_curr"]),
        "shortage": sum(1 for row in rows if row["amount_fact"] < row["amount_curr"]),
        "equal": sum(1 for row in rows if row["amount_fact"] == row["amount_curr"]),
        "skipped_unknown_ids": [],
        "inventory_id": None,
        "inventory_number": None,
        "posting_id": None,
        "posting_number": None,
        "posting_lines": 0,
        "skipped_posting_ids": [],
        "charge_id": None,
        "charge_number": None,
        "charge_lines": 0,
        "skipped_charge_ids": [],
        "inventory_held": False,
        "posting_held": False,
        "charge_held": False,
        "held_errors": [],
        "dry_run": dry_run,
        **empty_price_stats(),
    }
    if dry_run or not rows:
        summary.update(apply_kz_sale_prices(client, api_prices, cfg, dry_run=dry_run))
        return summary

    created = client.request(
        "post",
        "inventories",
        {
            "organization_id": cfg["org_id"],
            "store_id": cfg["store_id"],
            "author_employee_id": cfg["employee_id"],
            "responsible_employee_id": cfg["employee_id"],
            "currency_id": cfg["currency_id"],
            "held": 0,
            "comment": f"Синк CRM {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        },
    )
    inventory_id = str(_result_id(created) or "")
    if not inventory_id:
        raise BrStockInventoryError(f"Не удалось создать инвентаризацию: {created}")
    summary["inventory_id"] = inventory_id
    summary["inventory_number"] = _document_number(client, "inventories", inventory_id, created)[:32]

    skipped = []
    for row in rows:
        try:
            client.request(
                "post",
                "inventorygoods",
                {
                    "inventory_id": inventory_id,
                    "good_id": row["good_id"],
                    "amount_curr": row["amount_curr"],
                    "amount_fact": row["amount_fact"],
                    "price": _qty(costs.get(row["good_id"])),
                },
            )
        except BusinessRuOrderError:
            skipped.append(row["good_id"])
    summary["skipped_unknown_ids"] = skipped

    kept = [row for row in rows if row["good_id"] not in set(skipped)]
    surplus = surplus_rows(kept)
    shortage = shortage_rows(kept)
    summary["posting_lines"] = len(surplus)
    summary["charge_lines"] = len(shortage)

    if surplus:
        _create_adjustment_document(
            client,
            summary,
            cfg,
            inventory_id,
            kind="posting",
            lines=surplus,
            costs=costs,
        )
    if shortage:
        _create_adjustment_document(
            client,
            summary,
            cfg,
            inventory_id,
            kind="charge",
            lines=shortage,
            costs=costs,
        )
    hold_stock_documents(client, summary)
    summary.update(apply_kz_sale_prices(client, api_prices, cfg, dry_run=False))
    return summary


def _create_adjustment_document(client, summary, cfg, inventory_id, *, kind: str, lines: list[dict], costs: dict):
    if kind == "posting":
        model, goods_model, id_key = "postings", "postinggoods", "posting_id"
        comment = f"Излишки по инвентаризации {summary['inventory_number'] or inventory_id}"
        label = "оприходование"
    else:
        model, goods_model, id_key = "charges", "chargegoods", "charge_id"
        comment = f"Недостачи по инвентаризации {summary['inventory_number'] or inventory_id}"
        label = "списание"

    created = client.request(
        "post",
        model,
        {
            "organization_id": cfg["org_id"],
            "store_id": cfg["store_id"],
            "author_employee_id": cfg["employee_id"],
            "responsible_employee_id": cfg["employee_id"],
            "inventory_id": inventory_id,
            "currency_id": cfg["currency_id"],
            "held": 0,
            "comment": comment,
        },
    )
    record_id = str(_result_id(created) or "")
    if not record_id:
        raise BrStockInventoryError(f"Не удалось создать {label}: {created}")
    number = _document_number(client, model, record_id, created)[:32]
    if kind == "posting":
        summary["posting_id"] = record_id
        summary["posting_number"] = number
        skipped_key = "skipped_posting_ids"
    else:
        summary["charge_id"] = record_id
        summary["charge_number"] = number
        skipped_key = "skipped_charge_ids"

    existing = []
    try:
        existing = _document_goods(client, model, record_id)
    except BusinessRuOrderError:
        existing = []

    skipped = []
    if existing:
        for item in existing:
            line_id = item.get("id")
            try:
                good_id = int(item.get("good_id"))
            except (TypeError, ValueError):
                continue
            if not line_id:
                continue
            try:
                client.request(
                    "put",
                    goods_model,
                    {"id": line_id, "price": _qty(costs.get(good_id))},
                )
            except BusinessRuOrderError:
                skipped.append(good_id)
    else:
        for row in lines:
            try:
                client.request(
                    "post",
                    goods_model,
                    {
                        id_key: record_id,
                        "good_id": row["good_id"],
                        "amount": row["amount"],
                        "price": _qty(costs.get(row["good_id"])),
                    },
                )
            except BusinessRuOrderError:
                skipped.append(row["good_id"])
    summary[skipped_key] = skipped


def _document_goods(client: BusinessRuOrderClient, model: str, record_id) -> list[dict]:
    payload = client.request("get", model, {"id": record_id, "with_goods": 1})
    record = payload.get("result")
    if isinstance(record, list):
        record = next(
            (item for item in record if str(item.get("id")) == str(record_id)),
            record[0] if record else None,
        )
    if not isinstance(record, dict):
        return []
    goods = record.get("goods") or []
    return [item for item in goods if isinstance(item, dict)]


@contextmanager
def kz_stock_sync_lock():
    if connection.vendor != "postgresql":
        yield True
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [KZ_SYNC_LOCK_KEY])
        acquired = bool(cursor.fetchone()[0])
    try:
        yield acquired
    finally:
        if acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [KZ_SYNC_LOCK_KEY])


def kz_sync_is_due(enabled, interval_hours, last_run_at, now) -> bool:
    if not enabled:
        return False
    try:
        hours = int(interval_hours or 24)
    except (TypeError, ValueError):
        hours = 24
    hours = min(max(hours, KZ_SYNC_INTERVAL_MIN_HOURS), KZ_SYNC_INTERVAL_MAX_HOURS)
    if last_run_at is None:
        return True
    return now >= last_run_at + timedelta(hours=hours)


def _held_suffix(summary: dict, id_key: str, held_key: str) -> str:
    if not summary.get(id_key):
        return ""
    if summary.get(held_key):
        return " (проведено)"
    return " (не проведено)"


def sync_result_text(summary: dict) -> str:
    skipped = summary.get("skipped_unknown_ids") or []
    skipped_posting = summary.get("skipped_posting_ids") or []
    skipped_charge = summary.get("skipped_charge_ids") or []
    text = (
        f"склад {summary.get('store_id')}: остатки {summary.get('current_lines')}, "
        f"API {summary.get('api_lines')}, строк описи {summary.get('inventory_lines')}, "
        f"излишки {summary.get('surplus')}, недостачи {summary.get('shortage')}, "
        f"инвентаризация id={summary.get('inventory_id')}"
    )
    if summary.get("inventory_number"):
        text += f" № {summary['inventory_number']}"
    text += _held_suffix(summary, "inventory_id", "inventory_held")
    if summary.get("posting_id"):
        text += f", оприходование id={summary['posting_id']}"
        if summary.get("posting_number"):
            text += f" № {summary['posting_number']}"
        text += _held_suffix(summary, "posting_id", "posting_held")
    else:
        text += ", оприходование не создано (нет излишков)"
    if summary.get("charge_id"):
        text += f", списание id={summary['charge_id']}"
        if summary.get("charge_number"):
            text += f" № {summary['charge_number']}"
        text += _held_suffix(summary, "charge_id", "charge_held")
    else:
        text += ", списание не создано (нет недостач)"
    if skipped:
        text += f", пропущены комплекты id {skipped[:20]}"
    if skipped_posting:
        text += f", пропущены в оприходовании id {skipped_posting[:20]}"
    if skipped_charge:
        text += f", пропущены в списании id {skipped_charge[:20]}"
    text += (
        f", цены: обновлено {summary.get('prices_updated') or 0}"
        f", без изменений {summary.get('prices_unchanged') or 0}"
        f", ошибок {summary.get('prices_failed') or 0}"
        f", товаров {summary.get('prices_goods') or 0}"
    )
    if summary.get("prices_list_id"):
        text += f", назначение цен id={summary['prices_list_id']}"
        if summary.get("prices_list_number"):
            text += f" № {summary['prices_list_number']}"
    skipped_prices = summary.get("skipped_price_ids") or []
    if skipped_prices:
        text += f", цены пропущены {skipped_prices[:20]}"
    held_errors = summary.get("held_errors") or []
    if held_errors:
        text += f", проводка не удалась: {held_errors[:5]}"
    return text


def create_sync_log(summary: dict | None, *, ok: bool, message: str):
    from .models import ApiKzSync

    summary = summary or {}
    warehouse = str(summary.get("warehouse_code") or "KZ").upper()
    if warehouse not in {ApiKzSync.WAREHOUSE_KZ, ApiKzSync.WAREHOUSE_RU, ApiKzSync.WAREHOUSE_UZ}:
        warehouse = ApiKzSync.WAREHOUSE_KZ
    return ApiKzSync.objects.create(
        warehouse_code=warehouse,
        store_id=str(summary.get("store_id") or "")[:32],
        ok=ok,
        message=message[:4000],
        inventory_id=str(summary.get("inventory_id") or "")[:32],
        inventory_number=str(summary.get("inventory_number") or "")[:32],
        posting_id=str(summary.get("posting_id") or "")[:32],
        posting_number=str(summary.get("posting_number") or "")[:32],
        charge_id=str(summary.get("charge_id") or "")[:32],
        charge_number=str(summary.get("charge_number") or "")[:32],
        prices_updated=int(summary.get("prices_updated") or 0),
        prices_unchanged=int(summary.get("prices_unchanged") or 0),
        prices_failed=int(summary.get("prices_failed") or 0),
        prices_goods=int(summary.get("prices_goods") or 0),
        prices_list_id=str(summary.get("prices_list_id") or "")[:32],
        prices_list_number=str(summary.get("prices_list_number") or "")[:32],
    )


def execute_kz_stock_sync() -> dict:
    with kz_stock_sync_lock() as acquired:
        if not acquired:
            return {
                "busy": True,
                "ok": False,
                "message": "Синхронизация уже выполняется",
                "log": None,
                "summary": None,
            }
        summary = None
        try:
            summary = create_stock_inventory()
            if not summary.get("inventory_id"):
                raise BrStockInventoryError(
                    "Документ инвентаризации не создан: "
                    f"остатки {summary.get('current_lines')}, "
                    f"API {summary.get('api_lines')}, "
                    f"строк описи {summary.get('inventory_lines')}"
                )
        except BrStockInventoryError as extra:
            log = create_sync_log(summary, ok=False, message=str(extra))
            return {
                "busy": False,
                "ok": False,
                "message": str(extra),
                "log": log,
                "summary": summary,
            }
        except Exception as extra:
            message = f"Синхронизация не удалась: {extra}"
            log = create_sync_log(summary, ok=False, message=message)
            return {
                "busy": False,
                "ok": False,
                "message": message,
                "log": log,
                "summary": summary,
            }
        text = sync_result_text(summary)
        log = create_sync_log(summary, ok=True, message=text)
        return {
            "busy": False,
            "ok": True,
            "message": text,
            "log": log,
            "summary": summary,
        }


def run_scheduled_kz_stock_sync(now=None):
    from .models import ApiKzSync, ApiKzSyncSettings

    settings_row = ApiKzSyncSettings.load()
    last = ApiKzSync.objects.order_by("-run_at", "-id").first()
    now = now or timezone.now()
    if not kz_sync_is_due(
        settings_row.enabled,
        settings_row.interval_hours,
        last.run_at if last else None,
        now,
    ):
        return None
    return execute_kz_stock_sync()
