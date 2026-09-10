import hashlib
import json
from contextlib import contextmanager
from urllib.parse import urlencode
import requests
from datetime import datetime
from django.db import connection
from django.utils.timezone import make_aware

from .models import ImageModel, GroupOfGoods, GoodsModel

from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()


def load_evacode_env():
    src_dir = Path(__file__).resolve().parents[1]
    root_dir = Path(__file__).resolve().parents[2]
    load_dotenv(src_dir / ".env", override=False)
    if not (os.getenv("APP_ID") or "").strip() or not (os.getenv("API_SECRET") or "").strip():
        load_dotenv(root_dir / ".env", override=True)


load_evacode_env()


SYNC_LOCK_KEY = 87236401


def parse_weight_grams(value):
    if value is None or value == "":
        return None
    try:
        grams = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    return grams if grams >= 0 else None


@contextmanager
def catalog_sync_lock():
    if connection.vendor != "postgresql":
        yield
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(%s)", [SYNC_LOCK_KEY])
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [SYNC_LOCK_KEY])


def korea_free_stock(remains):
    for item in remains or []:
        store_name = ((item.get("store") or {}).get("name") or "")
        if "корея" not in store_name.lower():
            continue
        amount = item.get("amount") or {}
        total = float(amount.get("total") or 0)
        reserved = float(amount.get("reserved") or 0)
        return max(0, int(total - reserved))
    return None


class BusinessRuAPIClient:
    base_url = "https://a46291.business.ru/api/rest"

    def __init__(self):
        load_evacode_env()
        self.api_secret = (os.getenv("API_SECRET") or "").strip()
        self.app_id = (os.getenv("APP_ID") or "").strip()
        self.token = ""
        self.app_psw = ""
        self.params = {"app_id": self.app_id}
        if not self.app_id or not self.api_secret:
            raise ValueError("Не заданы APP_ID / API_SECRET для Business.Ru")
        self.repair_hash = self.get_hash(params={"app_id": self.app_id})
        self.set_token()

    def set_token(self) -> None:
        response = requests.get(
            f"{self.base_url}/repair.json?app_id={self.app_id}&app_psw={self.repair_hash}",
            timeout=30,
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(
                f"Business.Ru repair: не JSON ({response.status_code})"
            ) from exc
        if not response.ok or not isinstance(data, dict) or not data.get("token"):
            raise ValueError(f"Business.Ru repair: HTTP {response.status_code}")
        self.token = data["token"]
        self.app_psw = data.get("app_psw") or ""

    def get_hash(self, params: dict, token='') -> str:
        params = dict(sorted(params.items()))
        hashed = hashlib.md5((token + self.api_secret + urlencode(params)).encode()).hexdigest()
        return hashed

    def get_goods_group(self) -> list:
        hashed = self.get_hash(params=self.params, token=self.token)
        response = requests.get(f'{self.base_url}/groupsofgoods.json?app_id={self.app_id}&app_psw={hashed}')
        data = dict(json.loads(response.content))
        return data['result']

    def get_stores(self) -> list:
        hashed = self.get_hash(params=self.params, token=self.token)
        response = requests.get(f'{self.base_url}/stores.json?app_id={self.app_id}&app_psw={hashed}')
        print(response.content)
        data = dict(json.loads(response.content))
        return data['result']

    def get_goods(self, page: int = 1, with_remains: int = 1, filter_positive_free_remains: int = 1,
                  with_prices: int = 1, filter_positive_remains: int = 1, archive: int = 0, with_attributes: int = 1) -> list[dict]:
        params = {
            'app_id': self.app_id,
            'page': page,
            'with_prices': with_prices,
            'with_remains': with_remains,
            'filter_positive_free_remains': filter_positive_free_remains,
            'filter_positive_remains': filter_positive_remains,
            'archive': archive,
            'with_attributes': with_attributes
        }
        hashed = self.get_hash(params=params, token=self.token)
        print(f'{self.base_url}/goods.json?{urlencode(params)}&app_psw={hashed}')
        response = requests.get(f'{self.base_url}/goods.json?{urlencode(params)}&app_psw={hashed}')
        response.raise_for_status()
        data = dict(json.loads(response.content))
        if "result" not in data:
            raise ValueError("Business.Ru goods response has no result")
        return data["result"]

    def get_json(self, model: str, extra: dict | None = None) -> dict:
        params = {"app_id": self.app_id, **(extra or {})}
        hashed = self.get_hash(params=params, token=self.token)
        response = requests.get(
            f"{self.base_url}/{model}.json",
            params={**params, "app_psw": hashed},
            timeout=30,
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(
                f"Business.Ru {model}: не JSON ({response.status_code}) {response.text}"
            ) from exc
        if not response.ok:
            raise ValueError(f"Business.Ru {model}: HTTP {response.status_code} {data}")
        if isinstance(data, dict) and data.get("status") == "error":
            raise ValueError(
                data.get("error_text") or data.get("error_code") or f"Business.Ru {model}: {data}"
            )
        return data


def normalize_barcode(value) -> str:
    return "".join(str(value or "").split())


def _payload_list(payload) -> list:
    result = payload.get("result") if isinstance(payload, dict) else payload
    if result is None or result is False:
        return []
    if isinstance(result, list):
        return [item for item in result if item is not None]
    if isinstance(result, dict):
        return [result]
    return []


def serialize_business_ru_good(good: dict, scanned_barcode: str = "") -> dict:
    group_id = good.get("group_id")
    try:
        category = int(group_id) if group_id not in (None, "") else None
    except (TypeError, ValueError):
        category = group_id
    good_id = good.get("id")
    try:
        good_id = int(good_id)
    except (TypeError, ValueError):
        pass
    listed = []
    for item in good.get("barcodes") or []:
        if isinstance(item, dict):
            value = item.get("barcode") or item.get("value")
        else:
            value = item
        if value:
            listed.append(value)
    scanned = normalize_barcode(scanned_barcode)
    listed_normalized = [normalize_barcode(value) for value in listed]
    if scanned and (scanned == normalize_barcode(good.get("barcode")) or scanned in listed_normalized):
        barcode = scanned_barcode or good.get("barcode")
    else:
        barcode = good.get("barcode") or (listed[0] if listed else "")
    unit = good.get("unit") or good.get("measure") or ""
    if isinstance(unit, dict):
        unit = unit.get("name") or unit.get("abbreviation") or ""
    return {
        "id": good_id,
        "title": good.get("full_name") or good.get("name") or "",
        "part": good.get("part") or "",
        "barcode": barcode,
        "description": good.get("description") or "",
        "category": category,
        "type": good.get("type") or "",
        "weight": parse_weight_grams(good.get("weight")),
        "unit": unit or "",
    }


def _norm_price_name(value) -> str:
    return " ".join(str(value or "").lower().replace("ё", "е").replace(".", " ").split())


KRW_PRICE_NAMES = {
    "закупочная цена": "purchase_price",
    "официальная цена": "official_price",
    "розничная цена": "retail_price",
    "мелкий опт": "small_wholesale_price",
    "средний опт": "medium_wholesale_price",
    "крупный опт": "large_wholesale_price",
}


def _price_amount(value):
    if value in (None, ""):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if amount != amount:
        return None
    rounded = round(amount)
    if abs(amount - rounded) < 1e-9:
        return int(rounded)
    return amount


def _price_currency_text(price_type: dict) -> str:
    currency = price_type.get("currency") if isinstance(price_type.get("currency"), dict) else {}
    chunks = [
        currency.get("id"),
        currency.get("name"),
        currency.get("short_name"),
        currency.get("code"),
        currency.get("iso"),
        currency.get("symbol"),
        currency.get("abbreviation"),
        price_type.get("currency_id"),
        price_type.get("currency_name"),
        price_type.get("currency_short_name"),
    ]
    return " ".join(str(item or "") for item in chunks).lower()


def _accept_krw_price(price_type: dict) -> bool:
    text = _price_currency_text(price_type)
    if any(token in text for token in ("krw", "вон", "₩", "won")):
        return True
    if any(token in text for token in ("kzt", "тенге", "₸", "rub", "руб", "₽", "rur")):
        return False
    return True


def serialize_krw_prices(good: dict) -> dict:
    payload = {
        "id": good.get("id"),
        "purchase_price": None,
        "official_price": None,
        "recommended_price": None,
        "retail_price": None,
        "small_wholesale_price": None,
        "medium_wholesale_price": None,
        "large_wholesale_price": None,
    }
    try:
        payload["id"] = int(good.get("id"))
    except (TypeError, ValueError):
        pass
    for item in good.get("prices") or []:
        if not isinstance(item, dict):
            continue
        price_type = item.get("price_type") if isinstance(item.get("price_type"), dict) else {}
        if not _accept_krw_price(price_type):
            continue
        field = KRW_PRICE_NAMES.get(_norm_price_name(price_type.get("name")))
        if not field or payload.get(field) is not None:
            continue
        amount = _price_amount(item.get("price"))
        if amount is None:
            continue
        payload[field] = amount
    return payload


def apply_current_prices(payload: dict, rows: list, type_id_to_field: dict) -> dict:
    for row in rows:
        if not isinstance(row, dict):
            continue
        field = type_id_to_field.get(str(row.get("price_type_id") or ""))
        if not field or payload.get(field) is not None:
            continue
        amount = _price_amount(row.get("price"))
        if amount is None:
            continue
        payload[field] = amount
    return payload


def buy_price_type_fields(types: list) -> dict:
    mapping = {}
    for item in types:
        if not isinstance(item, dict):
            continue
        field = KRW_PRICE_NAMES.get(_norm_price_name(item.get("name")))
        if not field:
            continue
        type_id = item.get("id")
        if type_id in (None, ""):
            continue
        mapping[str(type_id)] = field
    return mapping


class BusinessRuGoodPricesLookup:
    def __init__(self, api_client=None):
        self.api_client = api_client or BusinessRuAPIClient()

    def get(self, good_id) -> dict | None:
        try:
            wanted = int(good_id)
        except (TypeError, ValueError):
            return None
        items = _payload_list(
            self._payload(
                "goods",
                {
                    "id": wanted,
                    "with_prices": 1,
                },
            )
        )
        good = next(
            (item for item in items if isinstance(item, dict) and str(item.get("id")) == str(wanted)),
            None,
        )
        if not good:
            return None
        payload = serialize_krw_prices(good)
        self._fill_buy_prices(payload, wanted)
        return payload

    def _fill_buy_prices(self, payload: dict, wanted: int) -> None:
        try:
            types = _payload_list(self.api_client.get_json("buypricetypes", {}))
            rows = _payload_list(
                self.api_client.get_json("currentprices", {"good_id": wanted})
            )
        except ValueError:
            return
        apply_current_prices(payload, rows, buy_price_type_fields(types))

    def _payload(self, model: str, extra: dict) -> dict:
        try:
            return self.api_client.get_json(model, extra)
        except ValueError as extra_err:
            text = str(extra_err).lower()
            if any(token in text for token in ("unknown model", "не найден", "not found", "does not exist")):
                return {"result": []}
            raise


class BusinessRuBarcodeLookup:
    def __init__(self, api_client=None):
        self.api_client = api_client or BusinessRuAPIClient()

    def find(self, barcode: str) -> dict | None:
        goods = self.find_all(barcode)
        return goods[0] if goods else None

    def find_all(self, barcode: str) -> list[dict]:
        code = normalize_barcode(barcode)
        if not code:
            return []
        found = []
        seen = set()
        had_barcode_rows = False
        for item in self._results("barcodes", {"value": code}):
            item_code = item.get("value") or item.get("barcode")
            if normalize_barcode(item_code) != code:
                continue
            had_barcode_rows = True
            if item.get("deleted") in (True, 1, "1"):
                continue
            good = self._get_good(item.get("good_id") or item.get("goods_id"))
            self._append_unique(found, seen, good, item_code)
        if had_barcode_rows:
            return found
        for hit in self._goodssearch_hits(code):
            if not hit.get("barcode_found"):
                continue
            good = self._get_good(hit.get("good_id") or hit.get("id"))
            self._append_unique(found, seen, good, code)
        return found

    @staticmethod
    def _append_unique(found: list, seen: set, good: dict | None, barcode: str) -> bool:
        if not good:
            return False
        if BusinessRuBarcodeLookup._is_archived(good):
            return False
        good_id = str(good.get("id") or "")
        if not good_id or good_id in seen:
            return False
        seen.add(good_id)
        found.append({**good, "barcode": barcode})
        return True

    def _get_good(self, good_id) -> dict | None:
        if good_id in (None, ""):
            return None
        items = self._results(
            "goods",
            {
                "id": good_id,
                "with_attributes": 1,
                "archive": 0,
            },
        )
        good = items[0] if items else None
        if good and self._is_archived(good):
            return None
        return good

    @staticmethod
    def _is_archived(good: dict) -> bool:
        archive = good.get("archive")
        if archive in (True, 1, "1"):
            return True
        if str(archive).strip().lower() in ("true", "yes"):
            return True
        return good.get("deleted") in (True, 1, "1")

    def _goodssearch_hits(self, code: str) -> list:
        try:
            payload = self.api_client.get_json("goodssearch", {"text": code})
        except ValueError as exc:
            if self._unknown_model(str(exc)) or "text" in str(exc).lower():
                return []
            raise
        result = payload.get("result") if isinstance(payload, dict) else payload
        goods = result.get("goods") if isinstance(result, dict) else result
        if isinstance(goods, dict):
            return [item for item in goods.values() if isinstance(item, dict)]
        if isinstance(goods, list):
            return [item for item in goods if isinstance(item, dict)]
        return []

    def _results(self, model: str, extra: dict) -> list:
        try:
            payload = self.api_client.get_json(model, extra)
        except ValueError as exc:
            if self._unknown_model(str(exc)):
                return []
            raise
        return [item for item in _payload_list(payload) if isinstance(item, dict)]

    @staticmethod
    def _unknown_model(message: str) -> bool:
        text = (message or "").lower()
        return any(token in text for token in ("unknown model", "не найден", "not found", "does not exist"))


class BusinessRuService:
    def __init__(self, api_client=None):
        self.api_client = api_client or BusinessRuAPIClient()

    def group_to_model(self):
        group_data = self.api_client.get_goods_group()
        for group in group_data:
            datestr = group["updated"][:19] if len(group["updated"]) >= 21 else group["updated"]
            datetime_object = datetime.strptime(datestr, '%d.%m.%Y %H:%M:%S')
            updated_aware = make_aware(datetime_object)
            defaults = {
                'id': int(group['id']),
                'default_order': group['default_order'],
                'deleted': group['deleted'],
                'description': group['description'],
                'name': group['name'],
                'parent_id_id': group['parent_id'],
                'updated': updated_aware
            }
            obj, created = GroupOfGoods.objects.update_or_create(id=int(group['id']), defaults=defaults,
                                                                 create_defaults=defaults)
            if created:
                raw = str(group.get('default_order') or '').strip()
                if raw.lstrip('-').isdigit():
                    obj.site_order = int(raw)
                    obj.save(update_fields=['site_order'])
                else:
                    obj.save()
            if group['images']:
                for image in group['images']:
                    image_object = ImageModel.objects.get_or_create(
                        name=image['name'],
                        url=image['url'],
                        sort=image['sort'],
                        group_id=group['id']
                    )
                    if not (isinstance(image_object, tuple)):
                        image_object.save()

    def _goods_defaults(self, good, stock):
        defaults = {
            "title": good.get("full_name") or good.get("name") or "",
            "description": good.get("description"),
            "category_id": int(good["group_id"]),
            "type": good.get("type") or "",
            "stock": stock,
            "weight": parse_weight_grams(good.get("weight")),
            "bestseller": self.get_bestseller_value(good.get("attributes") or []),
        }
        for price in good.get("prices") or []:
            match (price.get("price_type") or {}).get("name"):
                case "Оптовая Цена":
                    defaults["wholesale_price"] = price.get("price")
                case "Крупный опт":
                    defaults["large_wholesale_price"] = price.get("price")
                case "Официальная Цена":
                    defaults["official_price"] = price.get("price")
                case "Розничная Цена":
                    defaults["retail_price"] = price.get("price")
        return defaults

    def _sync_good_images(self, good_id, images):
        keep_urls = []
        for image in images or []:
            url = image.get("url")
            if not url:
                continue
            keep_urls.append(url)
            ImageModel.objects.update_or_create(
                good_id=good_id,
                url=url,
                defaults={
                    "name": image.get("name") or "",
                    "sort": image.get("sort"),
                },
            )
        stale = ImageModel.objects.filter(good_id=good_id)
        if keep_urls:
            stale = stale.exclude(url__in=keep_urls)
        stale.delete()

    def goods_to_model(self):
        with catalog_sync_lock():
            self._goods_to_model()

    def _goods_to_model(self):
        page = 1
        active_ids = set()
        created_count = 0
        updated_count = 0
        hidden_count = 0
        completed = False
        try:
            while True:
                goods_data = self.api_client.get_goods(page=page)
                if not goods_data:
                    break
                for good in goods_data:
                    try:
                        good_id = int(good["id"])
                        group_id = int(good["group_id"])
                    except (KeyError, TypeError, ValueError):
                        print(f"Skip good with invalid id/group: {good.get('id')}")
                        continue
                    free_stock = korea_free_stock(good.get("remains"))
                    exists = GoodsModel.objects.filter(id=good_id).exists()
                    if free_stock is None or free_stock <= 0:
                        if exists:
                            GoodsModel.objects.filter(id=good_id).update(stock=0)
                            hidden_count += 1
                        continue
                    if not GroupOfGoods.objects.filter(id=group_id).exists():
                        print(f"Skip good {good_id}: category {group_id} is missing")
                        continue
                    defaults = self._goods_defaults(good, free_stock)
                    _obj, created = GoodsModel.objects.update_or_create(
                        id=good_id,
                        defaults=defaults,
                    )
                    self._sync_good_images(good_id, good.get("images"))
                    if created:
                        from .product_content import apply_product_content

                        apply_product_content(_obj, force=False)
                    active_ids.add(good_id)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                page += 1
            completed = True
        finally:
            if completed:
                extra_hidden = (
                    GoodsModel.objects.exclude(id__in=active_ids)
                    .exclude(stock=0)
                    .update(stock=0)
                )
                hidden_count += extra_hidden
                print(
                    "Goods sync finished: "
                    f"created={created_count} updated={updated_count} hidden={hidden_count}"
                )
            else:
                print("Goods sync aborted, existing stock was not bulk-hidden")

    def get_bestseller_value(self, attrs: list) -> int:
        for attr in attrs:
            if attr['attribute'].get('name').lower() == 'bestseller':
                print(attr['value'].get('name', 0))
                if attr['value'].get('name', 0).lower() == 'да':
                    return 1
        return 0
