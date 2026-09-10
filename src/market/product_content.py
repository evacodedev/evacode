from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

from django.utils.text import slugify

from .models import (
    GoodsModel,
    ProductBrand,
    ProductBrandI18n,
    ProductContent,
    ProductContentBlock,
    ProductContentBlockI18n,
    ProductKind,
    ProductKindI18n,
)

HEADING_TO_KIND = (
    (re.compile(r"^преимущества\s*:?\s*$", re.IGNORECASE), "benefits", "Преимущества"),
    (re.compile(r"^основные компоненты\s*:?\s*$", re.IGNORECASE), "ingredients", "Основные компоненты"),
    (re.compile(r"^текстура(?:\s+и\s+финиш)?\s*:?\s*$", re.IGNORECASE), "texture", "Текстура и финиш"),
    (re.compile(r"^способ применения\s*:?\s*$", re.IGNORECASE), "how_to_use", "Способ применения"),
    (re.compile(r"^подходит для\s*:?\s*$", re.IGNORECASE), "suitable_for", "Подходит для"),
)

INLINE_VOLUME = re.compile(r"^объ[её]м\s*:\s*(.+)$", re.IGNORECASE)
INLINE_WEIGHT = re.compile(r"^вес\s*:\s*(.+)$", re.IGNORECASE)

KIND_KEYWORDS = (
    ("lipstick", "губная помада", ("губная помада", "помада")),
    ("eye_cream", "крем для глаз", ("крем для глаз", "для глаз")),
    ("sunscreen", "солнцезащита", ("солнцезащит", "санскрин", "spf")),
    ("cleanser", "средство для умывания", ("гель для умывания", "пенка", "очищающ")),
    ("ampoule", "ампула", ("ампула",)),
    ("serum", "сыворотка", ("сыворотка",)),
    ("essence", "эссенция", ("эссенция",)),
    ("toner", "тонер", ("тонер",)),
    ("lotion", "лосьон", ("лосьон",)),
    ("patch", "патчи", ("патч",)),
    ("pad", "пэды", ("пэд", "toner pad")),
    ("mask", "маска", ("маска", "peel-off", "peel off")),
    ("powder", "пудра", ("пудра",)),
    ("cream", "крем", ("крем",)),
)

SECTION_HEADINGS_RU = {
    "lead": "",
    "about": "",
    "benefits": "Преимущества",
    "ingredients": "Основные компоненты",
    "texture": "Текстура и финиш",
    "how_to_use": "Способ применения",
    "suitable_for": "Подходит для",
    "volume": "Объём",
    "weight": "Вес",
    "rest": "",
}


class _HtmlText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []

    def handle_data(self, data):
        self.chunks.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5"}:
            self.chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5"}:
            self.chunks.append("\n")


EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0001F1E6-\U0001F1FF"
    "\U0000200D"
    "\U000020E3"
    "]+"
)


def strip_html(value) -> str:
    if not value:
        return ""
    parser = _HtmlText()
    parser.feed(unescape(str(value)))
    parser.close()
    lines = []
    for raw in "".join(parser.chunks).splitlines():
        line = EMOJI_RE.sub("", raw)
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _heading_kind(line: str):
    for pattern, kind, heading in HEADING_TO_KIND:
        if pattern.match(line):
            return kind, heading
    return None, ""


def _split_items(kind: str, lines: list[str]) -> tuple[str, list]:
    cleaned = [line.lstrip("•*-–— ").strip() for line in lines if line.strip()]
    if kind == "ingredients":
        items = []
        for line in cleaned:
            parts = re.split(r"\s+[—–-]\s+", line, maxsplit=1)
            if len(parts) == 2:
                items.append({"name": parts[0].strip(), "text": parts[1].strip()})
            else:
                items.append({"name": line, "text": ""})
        return "", items
    if kind in {"benefits", "how_to_use"}:
        return "", cleaned
    return "\n".join(cleaned), []


def _brand_from_title(title: str) -> str:
    text = (title or "").strip()
    if not text:
        return ""
    if ". " in text:
        head, _tail = text.split(". ", 1)
        if 1 < len(head) <= 48:
            return head.strip()
    return ""


def _kind_from_text(blob: str) -> tuple[str, str]:
    lowered = blob.lower()
    for slug, name_ru, needles in KIND_KEYWORDS:
        if any(needle in lowered for needle in needles):
            return slug, name_ru
    return "", ""


def parse_product_description(title: str, description: str) -> dict:
    plain = strip_html(description)
    title = (title or "").strip()
    lines = plain.splitlines() if plain else []
    buckets: dict[str, list[str]] = {}
    current = "intro"
    buckets[current] = []
    for line in lines:
        volume = INLINE_VOLUME.match(line)
        if volume:
            buckets.setdefault("volume", []).append(volume.group(1).strip())
            continue
        weight = INLINE_WEIGHT.match(line)
        if weight:
            buckets.setdefault("weight", []).append(weight.group(1).strip())
            continue
        kind, _heading = _heading_kind(line)
        if kind:
            current = kind
            buckets.setdefault(current, [])
            continue
        buckets.setdefault(current, []).append(line)

    intro_lines = buckets.pop("intro", [])
    product_hint = title.split(". ", 1)[-1] if ". " in title else title
    hint_matches = []
    eto_matches = []
    hint = product_hint[:24].lower() if product_hint else ""
    for line in intro_lines:
        lowered = line.lower()
        if hint and len(hint) >= 8 and hint in lowered:
            hint_matches.append(line)
        elif " это " in f" {lowered}":
            eto_matches.append(line)
    lead_line = (hint_matches[-1] if hint_matches else "") or (eto_matches[-1] if eto_matches else "")
    if not lead_line and intro_lines:
        lead_line = intro_lines[0]
    about_lines = list(intro_lines)

    blocks = []
    if lead_line:
        blocks.append({"kind": "lead", "heading": "", "body": lead_line, "items": []})
    if about_lines:
        blocks.append(
            {
                "kind": "about",
                "heading": "",
                "body": "\n".join(about_lines),
                "items": [],
            }
        )

    order = (
        "benefits",
        "ingredients",
        "texture",
        "how_to_use",
        "suitable_for",
        "volume",
        "weight",
        "rest",
    )
    leftover_keys = [key for key in buckets if key not in set(order)]
    for kind in list(order) + leftover_keys:
        lines_for = buckets.get(kind) or []
        if not lines_for:
            continue
        body, items = _split_items(kind, lines_for)
        blocks.append(
            {
                "kind": kind if kind in SECTION_HEADINGS_RU else "rest",
                "heading": SECTION_HEADINGS_RU.get(kind, ""),
                "body": body,
                "items": items,
            }
        )

    blob = f"{title}\n{plain}"
    brand_name = _brand_from_title(title)
    if not brand_name and plain:
        first = plain.split("\n", 1)[0]
        brand_name = _brand_from_title(first) or ""
        if not brand_name:
            match = re.match(r"^([^—\n]{2,48})\s+—\s+", first)
            if match and "это" not in match.group(1).lower():
                brand_name = match.group(1).strip()
    kind_slug, kind_name = _kind_from_text(blob)
    return {
        "brand_name": brand_name,
        "kind_slug": kind_slug,
        "kind_name": kind_name,
        "blocks": blocks,
    }


def _ensure_brand(name: str) -> ProductBrand | None:
    name = (name or "").strip()
    if not name:
        return None
    slug = slugify(name, allow_unicode=True) or slugify(name) or "brand"
    brand, created = ProductBrand.objects.get_or_create(slug=slug)
    if created or not brand.translations.filter(language="ru").exists():
        ProductBrandI18n.objects.get_or_create(
            brand=brand,
            language="ru",
            defaults={"name": name},
        )
    return brand


def _ensure_kind(slug: str, name_ru: str) -> ProductKind | None:
    if not slug:
        return None
    kind, created = ProductKind.objects.get_or_create(slug=slug)
    if created or not kind.translations.filter(language="ru").exists():
        ProductKindI18n.objects.get_or_create(
            kind=kind,
            language="ru",
            defaults={"name": name_ru or slug},
        )
    return kind


def apply_product_content(good: GoodsModel, *, force: bool = False) -> str:
    if not force and ProductContent.objects.filter(good=good).exists():
        return "skipped"
    parsed = parse_product_description(good.title, good.description or "")
    content, _created = ProductContent.objects.get_or_create(good=good)
    brand = _ensure_brand(parsed["brand_name"])
    kind = _ensure_kind(parsed["kind_slug"], parsed["kind_name"])
    update_fields = []
    if brand is not None and good.content_brand_id != brand.id:
        good.content_brand = brand
        update_fields.append("content_brand")
    if kind is not None and good.content_kind_id != kind.id:
        good.content_kind = kind
        update_fields.append("content_kind")
    if update_fields:
        good.save(update_fields=update_fields)

    wanted = {block["kind"] for block in parsed["blocks"]}
    existing = {block.kind: block for block in content.blocks.all()}
    for sort, payload in enumerate(parsed["blocks"]):
        block, _ = ProductContentBlock.objects.update_or_create(
            content=content,
            kind=payload["kind"],
            defaults={"sort": sort},
        )
        ProductContentBlockI18n.objects.update_or_create(
            block=block,
            language="ru",
            defaults={
                "heading": payload.get("heading") or "",
                "body": payload.get("body") or "",
                "items": payload.get("items") or [],
            },
        )
    for kind_key, block in existing.items():
        if kind_key in wanted:
            continue
        if block.translations.exclude(language="ru").exists():
            block.translations.filter(language="ru").delete()
        else:
            block.delete()
    content.save()
    return "parsed"


def parse_goods_queryset(queryset, *, force: bool = False) -> dict:
    parsed = 0
    skipped = 0
    for good in queryset.iterator():
        result = apply_product_content(good, force=force)
        if result == "skipped":
            skipped += 1
        else:
            parsed += 1
    return {"parsed": parsed, "skipped": skipped}
