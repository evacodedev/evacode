from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

from django.utils.text import slugify

from .models import (
    GoodsModel,
    ProductBrand,
    ProductContent,
    ProductContentBlock,
    ProductContentBlockI18n,
    ProductKind,
    ProductKindI18n,
)

HEADING_TO_KIND = (
    (re.compile(r"^преимущества\s*:?\s*$", re.IGNORECASE), "benefits", "Преимущества"),
    (re.compile(r"^3\s*free\s*:?\s*$", re.IGNORECASE), "benefits", "Преимущества"),
    (re.compile(r"^основные компоненты\s*:?\s*$", re.IGNORECASE), "ingredients", "Основные компоненты"),
    (re.compile(r"^особенности\b.*экстракт", re.IGNORECASE), "ingredients", "Основные компоненты"),
    (re.compile(r"^эффекты ухода за кожей\s+(.+)$", re.IGNORECASE), "ingredients", "Основные компоненты"),
    (re.compile(r"^текстура(?:\s+и\s+финиш)?\s*:?\s*$", re.IGNORECASE), "texture", "Текстура и финиш"),
    (re.compile(r"^способ применения\s*:?\s*$", re.IGNORECASE), "how_to_use", "Способ применения"),
    (re.compile(r"^рекомендуемый порядок применения\s*:?\s*$", re.IGNORECASE), "how_to_use", "Способ применения"),
    (re.compile(r"^подходит для\s*:?\s*$", re.IGNORECASE), "suitable_for", "Подходит для"),
    (re.compile(r"^что такое\b", re.IGNORECASE), "about", ""),
    (
        re.compile(r"^(в набор входит|состав набора|комплектация|состав линии)\s*:?\s*$", re.IGNORECASE),
        "set_contents",
        "Состав набора",
    ),
)

INLINE_VOLUME = re.compile(r"^объ[её]м\s*:\s*(.+)$", re.IGNORECASE)
INLINE_WEIGHT = re.compile(r"^вес\s*:\s*(.+)$", re.IGNORECASE)
INLINE_HOW_TO = re.compile(r"^способ применения\s*:\s+(.+)$", re.IGNORECASE)
SET_ITEM_RE = re.compile(r"^(\d{1,2})\.\s+(.+)$")
EFFECTS_INGREDIENT_RE = re.compile(r"^эффекты ухода за кожей\s+(.+)$", re.IGNORECASE)
BAD_LEAD_RE = re.compile(
    r"минеральн\w*\s+масл|парабен|триэтаноламин|\btea\b|нитрозамин",
    re.IGNORECASE,
)
SUITABLE_LINE_RE = re.compile(
    r"подходит для тех|подходящ\w{0,10} для чувствительн",
    re.IGNORECASE,
)

KIND_KEYWORDS = (
    ("set", "набор", ("special set", "6pcs", "pcs set", "набор", "комплект")),
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
    "set_contents": "Состав набора",
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


def _looks_like_set_item(line: str) -> bool:
    match = SET_ITEM_RE.match(line.strip())
    if not match:
        return False
    payload = match.group(2)
    if re.search(r"[A-Za-z]{3,}", payload) and re.search(r"[—–(-]| - ", payload):
        return True
    return bool(
        re.search(
            r"(тоник|тонер|крем|сыворотк|эмульси|ампул|эссенц|маска|набор)",
            payload,
            re.IGNORECASE,
        )
    )


def _append_item_text(item: dict, extra: str) -> None:
    extra = (extra or "").strip()
    if not extra:
        return
    current = (item.get("text") or "").strip()
    if not current:
        item["text"] = extra
        return
    if extra.lower() in current.lower():
        return
    item["text"] = f"{current.rstrip('.')} . {extra}".replace(" . ", ". ")


def _split_set_items(lines: list[str]) -> list:
    items: list[dict] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        numbered = SET_ITEM_RE.match(line)
        if numbered:
            payload = numbered.group(2).strip()
            parts = re.split(r"\s+[—–-]\s+", payload, maxsplit=1)
            items.append(
                {
                    "name": re.sub(r"\s+", " ", parts[0]).strip(),
                    "text": re.sub(r"\s+", " ", parts[1]).strip() if len(parts) == 2 else "",
                }
            )
            continue
        if not items:
            continue
        how = INLINE_HOW_TO.match(line)
        if how:
            _append_item_text(items[-1], how.group(1).strip())
            continue
        volume = INLINE_VOLUME.match(line)
        if volume:
            _append_item_text(items[-1], volume.group(1).strip())
            continue
        _append_item_text(items[-1], line)
    return items


def _split_items(kind: str, lines: list[str]) -> tuple[str, list]:
    if kind == "set_contents":
        return "", _split_set_items(lines)
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
    if kind == "benefits":
        items = []
        overflow = []
        for line in cleaned:
            if re.match(r"^(без|не содержит)\b", line, re.IGNORECASE) or len(line) <= 90:
                items.append(line)
            else:
                overflow.append(line)
        return "\n".join(overflow), items
    if kind == "how_to_use":
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
    token = re.match(r"^([A-Za-z][A-Za-z0-9&'’.-]{2,40})\b", text)
    if token and token.group(1).lower() not in {"the", "for", "and"}:
        return token.group(1)
    return ""


def _pick_lead(title: str, intro_lines: list[str]) -> str:
    product_hint = title.split(". ", 1)[-1] if ". " in title else title
    hint = product_hint[:24].lower() if product_hint else ""
    hint_matches = []
    story_matches = []
    usable = []
    for line in intro_lines:
        if BAD_LEAD_RE.search(line):
            continue
        lowered = line.lower()
        usable.append(line)
        if hint and len(hint) >= 8 and hint in lowered:
            hint_matches.append(line)
        if "представляет собой" in lowered or " это " in f" {lowered}":
            story_matches.append(line)
    return (
        (hint_matches[-1] if hint_matches else "")
        or (story_matches[0] if story_matches else "")
        or (usable[0] if usable else "")
    )


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
    pending_ingredient = ""
    for line in lines:
        how = INLINE_HOW_TO.match(line)
        if how:
            if pending_ingredient:
                buckets.setdefault("ingredients", []).append(pending_ingredient)
                pending_ingredient = ""
            if current == "set_contents":
                buckets.setdefault(current, []).append(line)
            else:
                buckets.setdefault("how_to_use", []).append(how.group(1).strip())
            continue
        volume = INLINE_VOLUME.match(line)
        if volume:
            if pending_ingredient:
                buckets.setdefault("ingredients", []).append(pending_ingredient)
                pending_ingredient = ""
            if current == "set_contents":
                buckets.setdefault(current, []).append(line)
            else:
                buckets.setdefault("volume", []).append(volume.group(1).strip())
            continue
        weight = INLINE_WEIGHT.match(line)
        if weight:
            if pending_ingredient:
                buckets.setdefault("ingredients", []).append(pending_ingredient)
                pending_ingredient = ""
            buckets.setdefault("weight", []).append(weight.group(1).strip())
            continue
        effect = EFFECTS_INGREDIENT_RE.match(line)
        if effect:
            if pending_ingredient:
                buckets.setdefault("ingredients", []).append(pending_ingredient)
            current = "ingredients"
            buckets.setdefault(current, [])
            pending_ingredient = effect.group(1).strip()
            continue
        kind, _heading = _heading_kind(line)
        if kind:
            if pending_ingredient:
                buckets.setdefault("ingredients", []).append(pending_ingredient)
                pending_ingredient = ""
            current = kind
            buckets.setdefault(current, [])
            if kind == "about":
                buckets[current].append(line)
            continue
        if _looks_like_set_item(line):
            if pending_ingredient:
                buckets.setdefault("ingredients", []).append(pending_ingredient)
                pending_ingredient = ""
            current = "set_contents"
            buckets.setdefault(current, []).append(line)
            continue
        if pending_ingredient:
            buckets.setdefault("ingredients", []).append(f"{pending_ingredient} — {line}")
            pending_ingredient = ""
            continue
        buckets.setdefault(current, []).append(line)
    if pending_ingredient:
        buckets.setdefault("ingredients", []).append(pending_ingredient)

    intro_lines = buckets.pop("intro", [])
    extra_about = buckets.pop("about", [])
    suitable_from_intro = []
    kept_intro = []
    for line in intro_lines:
        if SUITABLE_LINE_RE.search(line):
            suitable_from_intro.append(line)
        else:
            kept_intro.append(line)
    if suitable_from_intro:
        buckets.setdefault("suitable_for", [])
        buckets["suitable_for"] = suitable_from_intro + buckets["suitable_for"]

    lead_line = _pick_lead(title, kept_intro)
    about_lines = list(kept_intro) + extra_about

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
        "set_contents",
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
        if kind == "benefits" and body:
            buckets.setdefault("rest", []).append(body)
            body = ""
        if kind not in SECTION_HEADINGS_RU:
            kind = "rest"
        if not body and not items:
            continue
        blocks.append(
            {
                "kind": kind,
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
        "plain": plain,
    }


SHORT_COPY_CHARS = 250
EDITORIAL_KINDS = frozenset(
    {"benefits", "ingredients", "how_to_use", "texture", "suitable_for"}
)
ENRICHMENT_OK = "ok"
ENRICHMENT_NEEDED = "needs_enrichment"


def _has_ingredients(blocks: list) -> bool:
    for block in blocks:
        if block.get("kind") != "ingredients":
            continue
        items = block.get("items") or []
        body = (block.get("body") or "").strip()
        if items or body:
            return True
    return False


def assess_product_copy(title: str, description: str, parsed: dict | None = None) -> dict:
    parsed = parsed if parsed is not None else parse_product_description(title, description)
    plain = parsed.get("plain")
    if plain is None:
        plain = strip_html(description)
    kinds = {block.get("kind") for block in parsed.get("blocks") or []}
    reasons = []
    chars = len(plain)
    if chars == 0:
        reasons.append("empty")
    elif chars < SHORT_COPY_CHARS:
        reasons.append("short")
    if not (kinds & EDITORIAL_KINDS):
        reasons.append("no_sections")
    if not _has_ingredients(parsed.get("blocks") or []):
        reasons.append("no_ingredients")
    status = ENRICHMENT_NEEDED if reasons else ENRICHMENT_OK
    return {
        "status": status,
        "reasons": reasons,
        "char_count": chars,
        "section_kinds": sorted(kinds),
    }


def _lookup_brand(name: str) -> ProductBrand | None:
    name = (name or "").strip()
    if not name:
        return None
    slug = slugify(name, allow_unicode=True) or slugify(name)
    if slug:
        by_slug = ProductBrand.objects.filter(slug=slug).first()
        if by_slug:
            return by_slug
    matches = list(
        ProductBrand.objects.filter(translations__name__iexact=name).distinct()[:2]
    )
    if len(matches) == 1:
        return matches[0]
    return None


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
    assessment = assess_product_copy(good.title, good.description or "", parsed=parsed)
    content, _created = ProductContent.objects.get_or_create(good=good)
    content.enrichment_status = assessment["status"]
    content.enrichment_reasons = assessment["reasons"]
    kind = _ensure_kind(parsed["kind_slug"], parsed["kind_name"])
    update_fields = []
    if not good.content_brand_id:
        brand = _lookup_brand(parsed["brand_name"])
        if brand is not None:
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
    return "parsed" if assessment["status"] == ENRICHMENT_OK else ENRICHMENT_NEEDED


def refresh_enrichment_status(good: GoodsModel) -> dict:
    parsed = parse_product_description(good.title, good.description or "")
    assessment = assess_product_copy(good.title, good.description or "", parsed=parsed)
    content, _created = ProductContent.objects.get_or_create(good=good)
    content.enrichment_status = assessment["status"]
    content.enrichment_reasons = assessment["reasons"]
    content.save(update_fields=["enrichment_status", "enrichment_reasons"])
    return assessment


def parse_goods_queryset(queryset, *, force: bool = False, assess_only: bool = False) -> dict:
    parsed = 0
    skipped = 0
    assessed = 0
    needed = 0
    for good in queryset.iterator():
        if assess_only:
            assessment = refresh_enrichment_status(good)
            assessed += 1
            if assessment["status"] == ENRICHMENT_NEEDED:
                needed += 1
            continue
        result = apply_product_content(good, force=force)
        if result == "skipped":
            skipped += 1
        else:
            parsed += 1
            if result == ENRICHMENT_NEEDED:
                needed += 1
    return {
        "parsed": parsed,
        "skipped": skipped,
        "assessed": assessed,
        "needed": needed,
    }
