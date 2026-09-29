"""YML-фид для Яндекс Товаров: товары в наличии, цена в рублях по курсу витрины."""

import re
import xml.etree.ElementTree as ET
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Prefetch
from django.utils import timezone

from core.currency_pairs import get_quote_rate
from core.currency_pricing import round_quote_price
from market.models import GoodsModel, GroupOfGoods, ImageModel
from market.product_content import strip_html

SITE_URL = "https://evacode.co.kr"
FEED_CURRENCY = "RUB"
YML_CURRENCY = "RUR"
DESCRIPTION_MAX_LEN = 3000
PICTURES_PER_OFFER = 10
BUSINESS_RU_PREFIX = "https://a46291.business.ru/"
BRAND_NAME_LANGS = ("ru", "en", "ko")
FEED_CACHE_KEY = "market:yandex_feed"
FEED_CACHE_SECONDS = 3600

_XML_INVALID_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(value) -> str:
    return _XML_INVALID_RE.sub("", str(value or "")).strip()


def _picture_url(url: str) -> str:
    url = _clean(url)
    if url.startswith("http://a46291.business.ru/"):
        url = "https://" + url[len("http://"):]
    return url if url.startswith(BUSINESS_RU_PREFIX) else ""


def _brand_name(brand) -> str:
    if brand is None:
        return ""
    names = {item.language: item.name for item in brand.translations.all() if item.name}
    for lang in BRAND_NAME_LANGS:
        if names.get(lang):
            return names[lang]
    return brand.slug


def _description(raw: str) -> str:
    text = re.sub(r"\s+", " ", strip_html(raw or "")).strip()
    if len(text) <= DESCRIPTION_MAX_LEN:
        return text
    return text[:DESCRIPTION_MAX_LEN].rsplit(" ", 1)[0]


def _feed_goods():
    return (
        GoodsModel.objects.filter(stock__gt=0, retail_price__gt=0)
        .select_related("content_brand")
        .prefetch_related(
            "content_brand__translations",
            Prefetch("images", queryset=ImageModel.objects.order_by("sort", "id")),
        )
        .order_by("id")
    )


def _feed_categories(goods):
    groups = {group.id: group for group in GroupOfGoods.objects.all()}
    wanted = set()
    for good in goods:
        group_id = good.category_id
        while group_id and group_id not in wanted and group_id in groups:
            wanted.add(group_id)
            group_id = groups[group_id].parent_id_id
    return [groups[group_id] for group_id in sorted(wanted)]


def build_yandex_feed() -> bytes:
    rate = get_quote_rate(FEED_CURRENCY)
    goods = list(_feed_goods())
    categories = _feed_categories(goods)
    category_ids = {group.id for group in categories}

    root = ET.Element("yml_catalog", date=timezone.localtime().isoformat(timespec="minutes"))
    shop = ET.SubElement(root, "shop")
    ET.SubElement(shop, "name").text = "EvaCode"
    ET.SubElement(shop, "company").text = "EvaCode"
    ET.SubElement(shop, "url").text = f"{SITE_URL}/"

    currencies = ET.SubElement(shop, "currencies")
    ET.SubElement(currencies, "currency", id=YML_CURRENCY, rate="1")

    categories_el = ET.SubElement(shop, "categories")
    for group in categories:
        attrs = {"id": str(group.id)}
        if group.parent_id_id in category_ids:
            attrs["parentId"] = str(group.parent_id_id)
        ET.SubElement(categories_el, "category", attrs).text = _clean(group.name)

    offers = ET.SubElement(shop, "offers")
    for good in goods:
        price = round_quote_price(FEED_CURRENCY, Decimal(good.retail_price) * rate)
        offer = ET.SubElement(offers, "offer", id=str(good.id), available="true")
        ET.SubElement(offer, "name").text = _clean(good.title)
        brand = _brand_name(good.content_brand)
        if brand:
            ET.SubElement(offer, "vendor").text = _clean(brand)
        ET.SubElement(offer, "url").text = f"{SITE_URL}/product/{good.id}/"
        ET.SubElement(offer, "price").text = str(int(price))
        ET.SubElement(offer, "currencyId").text = YML_CURRENCY
        ET.SubElement(offer, "categoryId").text = str(good.category_id)
        pictures = [p for p in (_picture_url(img.url) for img in good.images.all()) if p]
        for picture in pictures[:PICTURES_PER_OFFER]:
            ET.SubElement(offer, "picture").text = picture
        description = _clean(_description(good.description))
        if description:
            ET.SubElement(offer, "description").text = description

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def cached_yandex_feed() -> bytes:
    body = cache.get(FEED_CACHE_KEY)
    if body is None:
        body = build_yandex_feed()
        cache.set(FEED_CACHE_KEY, body, FEED_CACHE_SECONDS)
    return body
