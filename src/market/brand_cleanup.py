"""Слить дубли брендов и убрать slug товаров из справочника."""

from django.db import transaction

from market.models import GoodsModel, ProductBrand, ProductBrandI18n

# Текущий slug канонической строки → (новый slug, имя на исконном языке).
CANONICAL = {
    "23skin-lab": ("23-skin-lab", "23 Skin Lab"),
    "SKIN U": ("skin-u", "SKIN U"),
    "pdhayi": ("pdhayi", "PDHAYi"),
    "the-history-of-whoo": ("the-history-of-whoo", "THE HISTORY OF WHOO"),
    "ch6": ("ch6", "CH6"),
    "vital-beautie": ("vital-beautie", "VITAL BEAUTIE"),
    "curacion": ("curacion", "Curación"),
    "o-hui": ("o-hui", "O HUI"),
    "sum37": ("sum37", "su:m37"),
    "cnp-laboratory": ("cnp-laboratory", "CNP Laboratory"),
    "gemmove": ("gemmove", "GEMMOVE"),
    "magnolia-ritual": ("magnolia-ritual", "Magnolia Ritual"),
    "i-envy": ("i-envy", "I-ENVY"),
    "amorepacific": ("amorepacific", "AMOREPACIFIC"),
    "hera": ("hera", "HERA"),
    "holitual": ("holitual", "HOLITUAL"),
    "sulwhasoo": ("sulwhasoo", "Sulwhasoo"),
    "ryo": ("ryo", "RYO"),
    "resuyeon": ("resuyeon", "RESUYEON"),
    "primera": ("primera", "Primera"),
    "median": ("median", "MEDIAN"),
    "hanami": ("hanami", "HANAMI"),
    "jaunkyeol": ("jaunkyeol", "JAUNKYEOL"),
    "troiareuke": ("troiareuke", "TROIAREUKE"),
    "biom美": ("biom美", "BIOM.美"),
    "tom-tit-tot": ("tom-tit-tot", "TOM-TIT-TOT"),
    "acfit": ("acfit", "ACFIT"),
    "salon-baekseo": ("salon-baekseo", "SALON BAEKSEO"),
    "venel": ("venel", "VENEL"),
    "infl": ("infl", "INFL"),
    "vital-garden": ("vital-garden", "Vital Garden"),
    "pink-c-romb": ("pink-c-romb", "Pink C Romb"),
    "glamfit": ("glamfit", "GLAMFIT"),
    "seolodam": ("seolodam", "Seolodam"),
    "calvisano": ("calvisano", "Calvisano"),
    "alpen-1618": ("alpen-1618", "Alpen 1618"),
    "fat-lab": ("fat-lab", "FAT LAB"),
    "oshiaree": ("oshiaree", "OSHIAREE"),
    "dr-cura": ("dr-cura", "Dr. Cura"),
    "dr-oregamo": ("dr-oregamo", "DR. Oregamo"),
}

# Источник-обрубок → несколько брендов по подстроке в названии товара.
SPLIT_BY_TITLE = {
    "dr": (
        ("dr-cura", "Dr. Cura", ("cura",)),
        ("dr-oregamo", "DR. Oregamo", ("oregamo",)),
    ),
}

# Лишний slug → канонический slug (как сейчас в базе, до переименования).
MERGE_INTO = {
    "hera-glow-lasting-24h-radiant-skin-foundation": "hera",
    "VITAL BEAUTY": "vital-beautie",
    "HERA": "holitual",
    "Primera": "primera",
    "Sulwhasoo": "sulwhasoo",
    "sulwhasoo-glowing-lip-balm": "sulwhasoo",
    "HOLITUAL": "holitual",
    "sensual-nude-balm": "hera",
    "sulwhasoo-men-daily-routine-2-items": "sulwhasoo",
    "антивозрастной-кушон": "amorepacific",
    "OHUI": "o-hui",
    "vital-garden-muscle-solution-fso": "vital-garden",
    "hera-lip-serum": "hera",
    "hera-rouge-classy": "hera",
    "o-hui-prime-advancer-pdrn-cooling-gel-pad": "o-hui",
    "repair-clinic-care-shampoo": "salon-baekseo",
    "tom-tit-tot-ttt-placenta-v15-shiny-ampoule": "tom-tit-tot",
    "sulwhasoo-perfecting-veil-primer-spf30-pa": "sulwhasoo",
    "hera-sensual-tinted-shine-lip-serum": "hera",
    "holitual-blue-pdrn-double-ampoule": "holitual",
    "hera-uv-protector-multi-defense": "hera",
    "hera-uv-protector-tone-up-lavender": "hera",
    "o-hui-ultimate-cover-collagen-lifting-bb-cream": "o-hui",
    "hera-comfy-conditioning-essence": "hera",
    "vital-garden-plant-based-melatonin-phyto-rest": "vital-garden",
    "o-hui-prime-advancer-de-aging-pdrn-booster-shot": "o-hui",
    "tom-tit-tot-ttt-tenseloid-cream": "tom-tit-tot",
    "primera-green-tea-intensive-hair-gift-set": "primera",
    "tom-tit-tot-ttt-tenseloid-ampoule": "tom-tit-tot",
    "sulwhasoo-first-care-set-3-items": "sulwhasoo",
    "vital-beautie-active-multi-pack": "vital-beautie",
    "vital-beautie-liver-prime-gold-30-days": "vital-beautie",
    "cnp-rx-after-op": "cnp-laboratory",
    "sulwhasoo-white-ginseng-exfoliating-mask": "sulwhasoo",
    "o-hui-age-recovery-essence": "o-hui",
    "sanarae-collagen-film-s": "23skin-lab",
    "hanami-the-more-bloom": "hanami",
    "m-pack-sanarae-collagen-film-s-23skin-lab": "23skin-lab",
    "m-pack-sanarae-collagen-film-s-2ea-23skin-lab": "23skin-lab",
    "ohui-the-first-geniture-skin-softener": "o-hui",
    "lv41-diy-cluster-lashes": "i-envy",
    "cnp-rx-blue-microlift-hydra-cream-special-set": "cnp-laboratory",
    "curación": "curacion",
    "sum-37": "sum37",
    "cnp-rx": "cnp-laboratory",
    "the-first-geniture": "o-hui",
    "lg-household-health-care": "vital-garden",
    "lg-life-garden": "vital-garden",
    "cnp": "cnp-laboratory",
    "lg-hh-vital-garden": "vital-garden",
    "life-garden": "vital-garden",
    "vital-beauty": "vital-beautie",
    "amore-pacific": "amorepacific",
    "vitalbeautie": "vital-beautie",
    "lg-vital-garden": "vital-garden",
    "ohui": "o-hui",
    "vital-garden-hanami": "vital-garden",
    "tom-tit-tot-ttt": "tom-tit-tot",
    "the-whoo": "the-history-of-whoo",
    "lg-household-healthcare": "vital-garden",
    "seol-o-dam": "seolodam",
    "m-pack": "oshiaree",
}


def _set_ru_name(brand: ProductBrand, name: str) -> None:
    ProductBrandI18n.objects.update_or_create(
        brand=brand,
        language="ru",
        defaults={"name": name},
    )


def _ensure_brand(brands: dict, slug: str, name: str, *, dry_run: bool) -> ProductBrand | None:
    brand = brands.get(slug)
    if brand:
        return brand
    if dry_run:
        return None
    brand = ProductBrand.objects.create(slug=slug)
    _set_ru_name(brand, name)
    brands[slug] = brand
    return brand


def _canonical_slugs() -> set[str]:
    return {item[0] for item in CANONICAL.values()}


def cleanup_product_brands(*, dry_run: bool = False) -> dict:
    brands = {brand.slug: brand for brand in ProductBrand.objects.all()}
    moved = []
    missing_target = []
    renamed = []
    named = []
    deleted = []

    def apply_merge(source: ProductBrand, target: ProductBrand) -> int:
        count = GoodsModel.objects.filter(content_brand=source).count()
        if dry_run:
            return count
        GoodsModel.objects.filter(content_brand=source).update(content_brand=target)
        source.delete()
        return count

    with transaction.atomic():
        for source_slug, target_slug in MERGE_INTO.items():
            source = brands.get(source_slug)
            if source is None:
                continue
            target = brands.get(target_slug)
            if target is None:
                missing_target.append(source_slug)
                continue
            count = apply_merge(source, target)
            moved.append((source_slug, target_slug, count))
            deleted.append(source_slug)
            brands.pop(source_slug, None)

        for source_slug, targets in SPLIT_BY_TITLE.items():
            source = brands.get(source_slug)
            if source is None:
                continue
            leftover_goods = 0
            for good in list(source.goods.all()):
                blob = (good.title or "").casefold()
                match = next(
                    (
                        (slug, name)
                        for slug, name, needles in targets
                        if any(needle in blob for needle in needles)
                    ),
                    None,
                )
                if match is None:
                    leftover_goods += 1
                    continue
                target_slug, target_name = match
                target = _ensure_brand(brands, target_slug, target_name, dry_run=dry_run)
                moved.append((source_slug, target_slug, 1))
                if not dry_run and target is not None:
                    good.content_brand = target
                    good.save(update_fields=["content_brand"])
            if leftover_goods == 0:
                deleted.append(source_slug)
                if not dry_run:
                    source.delete()
                brands.pop(source_slug, None)

        for old_slug, (new_slug, name) in CANONICAL.items():
            brand = brands.get(old_slug) or brands.get(new_slug)
            if brand is None:
                continue
            if brand.slug != new_slug:
                renamed.append((old_slug, new_slug))
                if not dry_run:
                    brand.slug = new_slug
                    brand.save(update_fields=["slug"])
                brands.pop(old_slug, None)
                brands[new_slug] = brand
            current = str(brand)
            if current != name:
                named.append((new_slug, current, name))
                if not dry_run:
                    _set_ru_name(brand, name)

        if dry_run:
            transaction.set_rollback(True)

    leftover = list(
        ProductBrand.objects.exclude(slug__in=_canonical_slugs()).order_by("id")
    )
    if dry_run:
        leftover = [
            brand
            for brand in ProductBrand.objects.all().order_by("id")
            if brand.slug not in CANONICAL
            and brand.slug not in MERGE_INTO
            and brand.slug not in SPLIT_BY_TITLE
        ]

    return {
        "moved": moved,
        "deleted": deleted,
        "renamed": renamed,
        "named": named,
        "missing_target": missing_target,
        "leftover": leftover,
    }
