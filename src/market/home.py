"""Homepage bundle: one payload for SSR instead of many catalog round-trips."""

from django.db.models import Count, F, Q

from .models import GoodsModel, ProductBrand, ProductKind
from .serializers import (
    GoodsListSerializer,
    _named_label,
    content_language_from_request,
    serialize_brand_page,
)

HOME_BRAND_SLUGS = ("curacion", "jogabi", "tom-tit-tot")
HOME_KIND_SECTIONS = (
    {"key": "set", "slugs": ("set",), "resolve_largest": False, "page_size": 9},
    {"key": "cream", "slugs": ("cream", "eye_cream"), "resolve_largest": True, "page_size": 9},
)


def _goods_qs():
    return (
        GoodsModel.objects.filter(stock__gt=0)
        .select_related("content_brand", "content_kind")
        .prefetch_related(
            "images",
            "content_brand__translations",
            "content_kind__translations",
        )
        .order_by(F("queue").asc(nulls_last=True), "title", "id")
        .distinct()
    )


def _serialize_goods(queryset, request, limit):
    items = list(queryset[:limit])
    return GoodsListSerializer(items, many=True, context={"request": request}).data


def _kind_counts(slugs):
    in_stock = Q(goods__stock__gt=0)
    rows = (
        ProductKind.objects.filter(slug__in=slugs)
        .annotate(count=Count("goods", filter=in_stock, distinct=True))
        .prefetch_related("translations")
    )
    return {item.slug: item for item in rows}


def _kind_section(lang, request, section):
    kinds = _kind_counts(section["slugs"])
    wanted = [kinds[slug] for slug in section["slugs"] if slug in kinds]
    if section["resolve_largest"] and wanted:
        chosen = max(wanted, key=lambda item: item.count or 0)
    elif wanted:
        chosen = wanted[0]
    else:
        chosen = None

    if chosen is None:
        label = {
            "slug": section["slugs"][0],
            "name": section["slugs"][0],
            "count": 0,
        }
        return {"chosen": label, "results": []}

    label = _named_label(chosen, lang) or {"slug": chosen.slug, "name": chosen.slug}
    label["count"] = chosen.count
    results = _serialize_goods(
        _goods_qs().filter(content_kind__slug=chosen.slug),
        request,
        section["page_size"],
    )
    return {"chosen": label, "results": results}


def _brand_section(lang, request, slug):
    brand = (
        ProductBrand.objects.filter(slug=slug, page_published=True)
        .prefetch_related("translations")
        .first()
    )
    brand_payload = serialize_brand_page(brand, lang) if brand else None
    results = _serialize_goods(
        _goods_qs().filter(content_brand__slug=slug),
        request,
        4,
    )
    return {"brand": brand_payload, "results": results}


def _recommend(request, bestsellers):
    hit_ids = {item["id"] for item in bestsellers}
    brands = []
    kinds = []
    for item in bestsellers:
        brand = item.get("content_brand") or {}
        kind = item.get("content_kind") or {}
        if brand.get("slug") and brand["slug"] not in brands:
            brands.append(brand["slug"])
        if kind.get("slug") and kind["slug"] not in kinds:
            kinds.append(kind["slug"])
        if len(brands) >= 6 and len(kinds) >= 6:
            break
    brands = brands[:6]
    kinds = kinds[:6]
    if not brands and not kinds:
        return []

    qs = _goods_qs().exclude(id__in=hit_ids)
    if brands:
        qs = qs.filter(content_brand__slug__in=brands)
    if kinds:
        qs = qs.filter(content_kind__slug__in=kinds)
    return _serialize_goods(qs, request, 9)


def build_home_page(request):
    lang = content_language_from_request(request)
    bestsellers = _serialize_goods(_goods_qs().filter(bestseller=True), request, 12)
    kinds = {
        section["key"]: _kind_section(lang, request, section)
        for section in HOME_KIND_SECTIONS
    }
    brands = {
        slug: _brand_section(lang, request, slug)
        for slug in HOME_BRAND_SLUGS
    }
    return {
        "bestsellers": bestsellers,
        "recommend": _recommend(request, bestsellers),
        "kinds": kinds,
        "brands": brands,
    }
