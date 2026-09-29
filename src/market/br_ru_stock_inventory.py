from contextlib import contextmanager
from datetime import datetime
import os

import requests
from django.conf import settings
from django.db import connection
from django.utils import timezone

from .br_stock_inventory import (
    BrStockInventoryError,
    _create_adjustment_document,
    _prices_equal,
    _qty,
    empty_price_stats,
    fetch_kz_purchase_prices,
    fetch_store_snapshot,
    hold_stock_documents,
    kz_sync_is_due,
    merge_inventory_rows,
    shortage_rows,
    surplus_rows,
)
from .business_ru_orders import BusinessRuOrderClient, BusinessRuOrderError, _document_number, _result_id
from .utils import load_evacode_env


RU_STORE_ID = "903587"
RUB_CURRENCY_ID = "1"
RU_PURCHASE_PRICE_TYPE_ID = "903632"
RU_SYNC_LOCK_KEY = 87236403
RU_STOCK_URL_DEFAULT = "https://evacode.ip-host.ru/evacode_trade11/hs/market/goods/"
RU_SALE_PRICE_TYPES = (
    ("price_wholesale_small", "BUSINESS_RU_RU_PRICE_TYPE_WHOLESALE_SMALL", "976958"),
    ("price_wholesale_medium", "BUSINESS_RU_RU_PRICE_TYPE_WHOLESALE_MEDIUM", "1710631"),
    ("price_wholesale_large", "BUSINESS_RU_RU_PRICE_TYPE_WHOLESALE_LARGE", "976962"),
    ("price_retail", "BUSINESS_RU_RU_PRICE_TYPE_RETAIL", "913538"),
)


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def ru_inventory_settings() -> dict:
    load_evacode_env()
    org_id = _env("BUSINESS_RU_ORGANIZATION_ID") or str(
        getattr(settings, "BUSINESS_RU_ORGANIZATION_ID", "") or ""
    ).strip()
    employee_id = _env("BUSINESS_RU_EMPLOYEE_ID") or str(
        getattr(settings, "BUSINESS_RU_EMPLOYEE_ID", "") or ""
    ).strip()
    return {
        "store_id": _env("BUSINESS_RU_RU_STORE_ID", RU_STORE_ID),
        "org_id": org_id,
        "employee_id": employee_id,
        "currency_id": _env("BUSINESS_RU_RU_CURRENCY_ID", RUB_CURRENCY_ID),
        "purchase_price_type_id": _env(
            "BUSINESS_RU_RU_PURCHASE_PRICE_TYPE_ID",
            RU_PURCHASE_PRICE_TYPE_ID,
        ),
        "stock_url": _env("RU_STOCK_URL", RU_STOCK_URL_DEFAULT),
        "stock_user": _env("RU_STOCK_USER"),
        "stock_password": _env("RU_STOCK_PASSWORD"),
        "sale_price_type_ids": {
            field: _env(env_name, default)
            for field, env_name, default in RU_SALE_PRICE_TYPES
        },
    }


def parse_ru_catalog(payload) -> tuple[dict[int, float], dict[int, dict[str, float]]]:
    if isinstance(payload, dict):
        products = payload.get("products")
    else:
        products = payload
    quantities = {}
    prices = {}
    fields = tuple(item[0] for item in RU_SALE_PRICE_TYPES)
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


def parse_ru_stock(payload) -> dict[int, float]:
    quantities, _ = parse_ru_catalog(payload)
    return quantities


def fetch_ru_catalog(url: str, user: str, password: str) -> tuple[dict[int, float], dict[int, dict[str, float]]]:
    response = requests.get(url, auth=(user, password), timeout=60)
    try:
        payload = response.json()
    except ValueError as extra:
        raise BrStockInventoryError(
            f"RU stock: не JSON ({response.status_code}) {response.text[:500]}"
        ) from extra
    if not response.ok:
        raise BrStockInventoryError(f"RU stock: HTTP {response.status_code} {payload}")
    return parse_ru_catalog(payload)


def collect_ru_sale_price_changes(
    current_by_type: dict[str, dict[int, float]],
    api_prices: dict[int, dict[str, float]],
    type_ids: dict[str, str],
) -> tuple[dict[int, list[tuple[str, float]]], dict]:
    stats = empty_price_stats()
    changes: dict[int, list[tuple[str, float]]] = {}
    for good_id, row in api_prices.items():
        items: list[tuple[str, float]] = []
        changed = False
        for field, _env_name, _default in RU_SALE_PRICE_TYPES:
            type_id = str(type_ids.get(field) or "").strip()
            if not type_id or field not in row:
                continue
            new_price = _qty(row.get(field))
            if new_price <= 0:
                continue
            current = current_by_type.get(type_id, {}).get(good_id)
            if current is not None and _prices_equal(current, new_price):
                stats["prices_unchanged"] += 1
            else:
                changed = True
                stats["prices_updated"] += 1
            items.append((type_id, new_price))
        if changed and items:
            changes[good_id] = items
    return changes, stats


def apply_ru_sale_prices(
    client: BusinessRuOrderClient,
    api_prices: dict[int, dict[str, float]],
    cfg: dict,
    *,
    dry_run: bool = False,
) -> dict:
    type_ids = cfg.get("sale_price_type_ids") or {}
    wanted_ids = [
        str(type_ids.get(field) or "").strip()
        for field, _env_name, _default in RU_SALE_PRICE_TYPES
        if str(type_ids.get(field) or "").strip()
    ]
    current_by_type = {
        type_id: fetch_kz_purchase_prices(client, type_id)
        for type_id in dict.fromkeys(wanted_ids)
    }
    changes, stats = collect_ru_sale_price_changes(current_by_type, api_prices, type_ids)
    stats["prices_goods"] = len(changes)
    if dry_run or not changes:
        return stats

    column_ids = list(
        dict.fromkeys(type_id for items in changes.values() for type_id, _price in items)
    )
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


def ru_sync_result_text(summary: dict) -> str:
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
    if summary.get("inventory_id"):
        text += " (проведено)" if summary.get("inventory_held") else " (не проведено)"
    if summary.get("posting_id"):
        text += f", оприходование id={summary['posting_id']}"
        if summary.get("posting_number"):
            text += f" № {summary['posting_number']}"
        text += " (проведено)" if summary.get("posting_held") else " (не проведено)"
    else:
        text += ", оприходование не создано (нет излишков)"
    if summary.get("charge_id"):
        text += f", списание id={summary['charge_id']}"
        if summary.get("charge_number"):
            text += f" № {summary['charge_number']}"
        text += " (проведено)" if summary.get("charge_held") else " (не проведено)"
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


def create_ru_stock_inventory(client: BusinessRuOrderClient | None = None, *, dry_run: bool = False) -> dict:
    cfg = ru_inventory_settings()
    if not cfg["store_id"]:
        raise BrStockInventoryError("Не задан BUSINESS_RU_RU_STORE_ID")
    if not cfg["org_id"] or not cfg["employee_id"]:
        raise BrStockInventoryError(
            "Не заданы BUSINESS_RU_ORGANIZATION_ID / BUSINESS_RU_EMPLOYEE_ID"
        )
    if not cfg["stock_user"] or not cfg["stock_password"]:
        raise BrStockInventoryError("Не заданы RU_STOCK_USER / RU_STOCK_PASSWORD")

    client = client or BusinessRuOrderClient()
    current, _ignored_costs = fetch_store_snapshot(client, cfg["store_id"])
    api_qty, api_prices = fetch_ru_catalog(cfg["stock_url"], cfg["stock_user"], cfg["stock_password"])
    rows = merge_inventory_rows(current, api_qty)
    costs = fetch_kz_purchase_prices(client, cfg["purchase_price_type_id"])
    summary = {
        "store_id": cfg["store_id"],
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
        summary.update(apply_ru_sale_prices(client, api_prices, cfg, dry_run=dry_run))
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
            "comment": f"Синк 1C RU {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
    summary.update(apply_ru_sale_prices(client, api_prices, cfg, dry_run=False))
    return summary


@contextmanager
def ru_stock_sync_lock():
    if connection.vendor != "postgresql":
        yield True
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [RU_SYNC_LOCK_KEY])
        acquired = bool(cursor.fetchone()[0])
    try:
        yield acquired
    finally:
        if acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [RU_SYNC_LOCK_KEY])


def create_ru_sync_log(summary: dict | None, *, ok: bool, message: str):
    from .models import ApiRuSync

    summary = summary or {}
    return ApiRuSync.objects.create(
        store_id=str(summary.get("store_id") or "")[:32],
        ok=ok,
        message=message,
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


def execute_ru_stock_sync() -> dict:
    with ru_stock_sync_lock() as acquired:
        if not acquired:
            return {
                "busy": True,
                "ok": False,
                "message": "Синхронизация RU уже выполняется",
                "log": None,
                "summary": None,
            }
        summary = None
        try:
            summary = create_ru_stock_inventory()
            has_stock = bool(summary.get("inventory_id"))
            has_prices = bool(
                summary.get("prices_list_id")
                or summary.get("prices_updated")
                or summary.get("prices_unchanged")
            )
            if not has_stock and not has_prices:
                raise BrStockInventoryError(
                    "Документ инвентаризации не создан: "
                    f"остатки {summary.get('current_lines')}, "
                    f"API {summary.get('api_lines')}, "
                    f"строк описи {summary.get('inventory_lines')}"
                )
        except BrStockInventoryError as extra:
            log = create_ru_sync_log(summary, ok=False, message=str(extra))
            return {
                "busy": False,
                "ok": False,
                "message": str(extra),
                "log": log,
                "summary": summary,
            }
        except Exception as extra:
            message = f"Синхронизация RU не удалась: {extra}"
            log = create_ru_sync_log(summary, ok=False, message=message)
            return {
                "busy": False,
                "ok": False,
                "message": message,
                "log": log,
                "summary": summary,
            }
        text = ru_sync_result_text(summary)
        log = create_ru_sync_log(summary, ok=True, message=text)
        return {
            "busy": False,
            "ok": True,
            "message": text,
            "log": log,
            "summary": summary,
        }


def run_scheduled_ru_stock_sync(now=None):
    from .models import ApiRuSync, ApiRuSyncSettings

    settings_row = ApiRuSyncSettings.load()
    last = ApiRuSync.objects.order_by("-run_at", "-id").first()
    now = now or timezone.now()
    if not kz_sync_is_due(
        settings_row.enabled,
        settings_row.weekdays,
        settings_row.run_time,
        last.run_at if last else None,
        now,
    ):
        return None
    return execute_ru_stock_sync()
