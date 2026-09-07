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

load_dotenv()


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
    api_secret = os.getenv('API_SECRET')
    app_id = os.getenv('APP_ID')
    base_url = 'https://a46291.business.ru/api/rest'
    token = ''
    app_psw = ''
    params = {
        'app_id': app_id
    }

    def __init__(self):
        self.repair_hash = self.get_hash(params={'app_id': self.app_id})
        self.set_token()

    def set_token(self) -> None:
        response = requests.get(f'{self.base_url}/repair.json?app_id={self.app_id}&app_psw={self.repair_hash}')
        data = dict(json.loads(response.content))
        self.token = data['token']
        self.app_psw = data['app_psw']

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
