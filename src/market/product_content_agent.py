from __future__ import annotations

import json
import os
import re

import requests
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from .models import (
    GoodsModel,
    ProductBrand,
    ProductBrandI18n,
    ProductContent,
    ProductContentAgentSettings,
    ProductContentBlock,
    ProductContentBlockI18n,
)
from .product_content import (
    _lookup_brand,
    parse_product_description,
    refresh_enrichment_from_sections,
    strip_html,
)
from .product_content_prompt import (
    BRAND_SITE_RULES,
    DEFAULT_AGENT_PROMPT,
    extra_sites_for_text,
    official_site_for_text,
)

CATALOG_SOURCE = "catalog:description"

ALLOWED_KINDS = {
    "lead",
    "about",
    "benefits",
    "ingredients",
    "texture",
    "how_to_use",
    "suitable_for",
    "volume",
    "weight",
    "set_contents",
    "rest",
}


def _allowed_source(source: str) -> bool:
    value = (source or "").strip()
    if value.startswith("catalog:"):
        return True
    return value.startswith("http://") or value.startswith("https://")


class AgentConfigError(Exception):
    pass


class AgentRunError(Exception):
    pass


def _api_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or os.getenv("CONTENT_AGENT_OPENAI_KEY") or "").strip()


def _agent_proxies() -> dict | None:
    url = (os.getenv("CONTENT_AGENT_PROXY") or "").strip()
    if not url:
        return None
    return {"http": url, "https": url}


def _raise_openai_error(response: requests.Response) -> None:
    body = (response.text or "")[:500]
    if response.status_code == 403 and "unsupported_country_region_territory" in body:
        raise AgentRunError(
            "OpenAI отклонил IP сервера (страна не поддерживается). "
            "Нужен CONTENT_AGENT_PROXY в поддерживаемом регионе; "
            "не ставьте HTTPS_PROXY на весь контейнер server."
        )
    raise AgentRunError(f"OpenAI {response.status_code}: {body}")


def extract_json_object(text: str) -> dict:
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```\s*$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise AgentRunError("Модель не вернула JSON")
    blob = raw[start : end + 1].replace("\r\n", "\n").replace("\r", "\n")
    last_error = None
    for candidate in (blob, _repair_json(blob)):
        try:
            data = json.loads(candidate, strict=False)
        except json.JSONDecodeError as extra:
            last_error = extra
            continue
        if not isinstance(data, dict):
            raise AgentRunError("JSON агента должен быть объектом")
        return data
    snippet = ""
    if last_error is not None and last_error.pos is not None:
        snippet = blob[max(0, last_error.pos - 80) : last_error.pos + 80]
    raise AgentRunError(
        f"Некорректный JSON от модели: {last_error}. Фрагмент: {snippet!r}"
    )


def _repair_json(blob: str) -> str:
    fixed = (
        blob.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )
    fixed = re.sub(
        r'("(?:name|text|body|heading|source_url)":\s*")([^"\n]*)\("([^"]+)"\)',
        r"\1\2(\3)",
        fixed,
    )
    fixed = _escape_controls_in_strings(fixed)
    fixed = re.sub(r"}\s*{", "},{", fixed)
    fixed = re.sub(r"]\s*\[", "],[", fixed)
    return re.sub(r",(\s*[}\]])", r"\1", fixed)


def _escape_controls_in_strings(blob: str) -> str:
    out = []
    in_string = False
    escaped = False
    for char in blob:
        if in_string:
            if escaped:
                out.append(char)
                escaped = False
            elif char == "\\":
                out.append(char)
                escaped = True
            elif char == '"':
                out.append(char)
                in_string = False
            elif char == "\n":
                out.append("\\n")
            elif char == "\t":
                out.append("\\t")
            else:
                out.append(char)
        else:
            if char == '"':
                in_string = True
            out.append(char)
    return "".join(out)


def _output_text(payload: dict) -> str:
    if payload.get("output_text"):
        return str(payload["output_text"])
    chunks = []
    for item in payload.get("output") or []:
        for part in item.get("content") or []:
            if part.get("type") in {"output_text", "text"} and part.get("text"):
                chunks.append(part["text"])
    return "\n".join(chunks)


def call_content_llm(system_prompt: str, user_payload: str, model: str) -> str:
    key = _api_key()
    if not key:
        raise AgentConfigError("Нет OPENAI_API_KEY в окружении")
    session = requests.Session()
    session.trust_env = False
    response = session.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or "gpt-4.1-mini",
            "tools": [{"type": "web_search"}],
            "input": [
                {
                    "role": "developer",
                    "content": f"{system_prompt or DEFAULT_AGENT_PROMPT}\n\n{BRAND_SITE_RULES}",
                },
                {"role": "user", "content": user_payload},
            ],
        },
        timeout=180,
        proxies=_agent_proxies(),
    )
    if response.status_code >= 400:
        _raise_openai_error(response)
    data = response.json()
    text = _output_text(data)
    if not text.strip():
        raise AgentRunError("Пустой ответ модели")
    return text


def _user_payload(good: GoodsModel, pages: list | None = None) -> str:
    brand = ""
    if good.content_brand_id:
        brand = str(good.content_brand)
    hint = official_site_for_text(f"{good.title} {brand}")
    extra = extra_sites_for_text(f"{good.title} {brand}")
    extra_line = ""
    if extra:
        extra_line = (
            "also_search_sites: "
            + ", ".join(extra)
            + "\nДля Whoo ищи site:whoo-hk.com/en/productdetail + имя товара "
            "(пример imperial-youth-emulsion), не только главную бренда.\n"
        )
    official_line = (
        f"preferred_official_url: {hint}\n"
        f"{extra_line}"
        "Сначала официальный сайт бренда, затем also_search_sites, затем интернет. "
        "Если SKU нет на первом сайте — не останавливайся. "
        "Ищи по точному названию на английском И на корейском (한글, 화해, 올리브영). "
        "Корейские страницы не игнорировать: с них бери INCI и how-to, пиши секции по-русски. "
        "Пустой blocks запрещён, если ниже есть description_from_BR: разложи его по секциям, "
        f"для таких кусков source_url={CATALOG_SOURCE}.\n"
        if hint
        else (
            f"{extra_line}"
            "Ищи товар в интернете по точному названию на английском и на корейском (한글). "
            f"Если страниц мало — разложи description_from_BR, source_url={CATALOG_SOURCE}.\n"
        )
    )
    return (
        f"id: {good.id}\n"
        f"title: {good.title}\n"
        f"brand_already_set: {brand or '(пусто — можно предложить каноническое имя)'}\n"
        f"kind: {good.content_kind or ''}\n"
        f"weight_grams_from_catalog: {good.weight}\n"
        f"{official_line}"
        f"{_fetched_pages_block(pages)}"
        f"description_from_BR:\n{good.description or ''}\n"
    )


def _fetched_pages_block(pages: list | None) -> str:
    if not pages:
        return ""
    chunks = [
        "fetched_pages: ниже УЖЕ скачанный текст официальной карточки. "
        "Разложи его по lead/about/benefits/texture/how_to_use полностью, не в одно предложение. "
        "source_url = URL этой страницы. Переведи на русский, INCI оставь латиницей.\n"
    ]
    for url, body in pages:
        chunks.append(f"URL: {url}\n{body}\n")
    return "\n".join(chunks)


USAGE_SPLIT_RE = re.compile(
    r"(?:^|\n)\s*(?:"
    r"способ\s+(?:использования|применения)"
    r"|как\s+(?:использовать|наносить|применять)"
    r"|рекомендуем(?:ый)?\s+(?:порядок|способ)"
    r"|(?:[-•*]\s*)?в случае если"
    r"|(?:[-•*]\s*)?нанесите\b"
    r")[\s\S]*",
    re.IGNORECASE,
)
USAGE_STEP_RE = re.compile(r"(?=Способ\s+использования\s+\d)", re.IGNORECASE)
INGREDIENT_HEAD_RE = re.compile(
    r"^(?:[-•*]\s*)?(?:содержит\b|экстракт\b|бета-?глюкан|гиалурон)",
    re.IGNORECASE,
)
NAME_DASH_RE = re.compile(r"^(.{2,90}?)\s[-—–]\s+(.+)$", re.DOTALL)
TITLE_LINE_RE = re.compile(r"^[A-Z0-9][A-Z0-9 \-_.]{2,70}$")
INGREDIENT_NAME_HINTS = (
    "экстракт",
    "глюкан",
    "кислот",
    "гиалурон",
    "cooler",
    "ингредиент",
    "комплекс",
    "пептид",
    "масло",
)
BOX_NOTE_RE = re.compile(r"\([^)]*\)")
WHOO_PREFIXES = ("the history of whoo", "the whoo", "whoo")


def _detail_slugs(title: str, prefixes: tuple[str, ...] = ()) -> list[str]:
    core = BOX_NOTE_RE.sub(" ", title or "")
    core = re.sub(r"\s+", " ", core).strip()
    lowered = core.casefold()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            core = core[len(prefix) :].strip(" -–—")
            lowered = core.casefold()
    words = [word for word in re.split(r"\s+", core) if word]
    slugs = []
    for parts in (words, words[1:], words[-3:]):
        if not parts:
            continue
        slug = slugify(" ".join(parts))
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs


def _candidate_source_urls(good: GoodsModel) -> list[str]:
    title = good.title or ""
    blob = f"{title} {good.content_brand or ''}".casefold()
    urls: list[str] = []
    if "whoo" in blob or "더후" in blob:
        for slug in _detail_slugs(title, WHOO_PREFIXES):
            urls.append(f"https://whoo-hk.com/en/productdetail/{slug}")
            urls.append(f"https://themonodist.com/the-history-of-whoo-{slug}/")
    seen = []
    for url in urls:
        if url not in seen:
            seen.append(url)
    return seen


def _fetch_url_text(url: str) -> str:
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.get(
            url,
            timeout=20,
            headers={"User-Agent": "EvacodeContentAgent/1.0"},
            proxies=_agent_proxies(),
        )
    except requests.RequestException:
        return ""
    if response.status_code >= 400 or not response.text:
        return ""
    return strip_html(response.text)[:12000]


def _gather_source_pages(good: GoodsModel) -> list[tuple[str, str]]:
    pages = []
    for url in _candidate_source_urls(good)[:8]:
        text = _fetch_url_text(url)
        if len(text) >= 240:
            pages.append((url, text))
    return pages


def _peel_usage(body: str) -> tuple[str, str]:
    text = (body or "").strip()
    match = USAGE_SPLIT_RE.search(text)
    if not match:
        return text, ""
    return text[: match.start()].strip(), match.group(0).strip()


def _usage_items(text: str) -> list:
    chunks = [part.strip() for part in USAGE_STEP_RE.split(text or "") if part.strip()]
    if len(chunks) > 1:
        return chunks
    parts = [
        part.strip(" -•*")
        for part in re.split(r"(?=\bДалее\s+нанесите\b)", text or "", flags=re.IGNORECASE)
        if part.strip()
    ]
    return parts if len(parts) > 1 else []


def _clean_usage_text(text: str) -> str:
    return re.sub(r"^[-•*]+\s*", "", (text or "").strip())


def _is_title_line(line: str) -> bool:
    compact = re.sub(r"\s+", " ", (line or "").strip())
    return bool(TITLE_LINE_RE.match(compact))


def _looks_ingredient(chunk: str) -> bool:
    text = (chunk or "").strip()
    if INGREDIENT_HEAD_RE.match(text):
        return True
    match = NAME_DASH_RE.match(text)
    if not match:
        return False
    left = match.group(1).casefold()
    return any(hint in left for hint in INGREDIENT_NAME_HINTS)


def _ingredient_item(chunk: str) -> dict:
    text = re.sub(r"^[-•*]+\s*", "", (chunk or "").strip())
    text = re.sub(r"^содержит\s+", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^запатентованн\w*\s+ингредиент\s+", "", text, flags=re.IGNORECASE).strip()
    match = NAME_DASH_RE.match(text)
    if match:
        item = {"name": match.group(1).strip(" :."), "text": match.group(2).strip()}
    elif ":" in text[:120]:
        name, rest = text.split(":", 1)
        item = {"name": name.strip(" ."), "text": rest.strip()}
    else:
        sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
        if len(sentence) > 1:
            item = {"name": sentence[0].strip(" ."), "text": sentence[1].strip()}
        else:
            item = {"name": text[:90].rstrip(" ."), "text": ""}
    if (item.get("text") or "").casefold() == (item.get("name") or "").casefold():
        item["text"] = ""
    return item


def _topic_chunks(text: str) -> list[str]:
    raw = (text or "").replace("\r\n", "\n").strip()
    if not raw:
        return []
    parts = [part.strip() for part in re.split(r"\n+", raw) if part.strip()]
    if len(parts) == 1:
        parts = [
            part.strip()
            for part in re.split(
                r"(?<=[.!?])\s+(?=Содержит\b|Экстракт\b|Бета-?глюкан\b)",
                parts[0],
                flags=re.IGNORECASE,
            )
            if part.strip()
        ]
    return parts


def _ensure_kind(by_kind: dict, order: list, kind: str, source: str) -> dict:
    if kind not in by_kind:
        by_kind[kind] = {
            "kind": kind,
            "heading": "",
            "body": "",
            "items": [],
            "source_url": source or "",
        }
        order.append(kind)
    return by_kind[kind]


def _kind_weak(block: dict | None) -> bool:
    if not block:
        return True
    items = block.get("items") or []
    body = str(block.get("body") or "").strip()
    return not items and len(body) < 80


def _append_named_item(block: dict, item: dict) -> None:
    items = block.setdefault("items", [])
    name = (item.get("name") or "").casefold()
    for existing in items:
        if isinstance(existing, dict) and (existing.get("name") or "").casefold() == name:
            if item.get("text") and not existing.get("text"):
                existing["text"] = item["text"]
            return
    items.append(item)


def _redistribute_about(by_kind: dict, order: list) -> None:
    about = by_kind.get("about")
    if not about:
        return
    chunks = _topic_chunks(about.get("body") or "")
    if len(chunks) < 2 and not _looks_ingredient(about.get("body") or ""):
        return
    source = about.get("source_url") or ""
    leftover = []
    current_ing = None
    for chunk in chunks:
        if _is_title_line(chunk):
            continue
        peeled_only = ""
        if USAGE_SPLIT_RE.match(chunk) or USAGE_SPLIT_RE.match(chunk.lstrip("-•* ")):
            peeled_only = _clean_usage_text(chunk)
        if peeled_only:
            usage = _ensure_kind(by_kind, order, "how_to_use", source)
            if _kind_weak(usage):
                steps = _usage_items(peeled_only) or [peeled_only]
                usage["items"] = list(usage.get("items") or []) + [step for step in steps if step]
                usage["body"] = ""
                usage["source_url"] = usage.get("source_url") or source
            continue
        if _looks_ingredient(chunk):
            ingredients = _ensure_kind(by_kind, order, "ingredients", source)
            item = _ingredient_item(chunk)
            _append_named_item(ingredients, item)
            current_ing = item
            ingredients["source_url"] = ingredients.get("source_url") or source
            continue
        if current_ing and not _looks_ingredient(chunk):
            extra = chunk.lstrip("*• ").strip()
            if extra:
                current_ing["text"] = f"{current_ing.get('text') or ''} {extra}".strip()
            continue
        leftover.append(chunk)
        current_ing = None
    about["body"] = "\n\n".join(leftover).strip()
    if not about["body"] and not about.get("items"):
        by_kind.pop("about", None)
        if "about" in order:
            order.remove("about")


def _attach_usage(by_kind: dict, order: list, source_kind: str, peeled: str) -> None:
    if not peeled:
        return
    source_block = by_kind.get(source_kind) or {}
    usage = by_kind.get("how_to_use")
    if usage and (usage.get("body") or usage.get("items")):
        return
    steps = _usage_items(peeled)
    cleaned = _clean_usage_text(peeled)
    by_kind["how_to_use"] = {
        "kind": "how_to_use",
        "heading": "",
        "body": "" if (steps or cleaned) else peeled,
        "items": steps or ([cleaned] if cleaned else []),
        "source_url": source_block.get("source_url") or "",
    }
    if "how_to_use" not in order:
        order.append("how_to_use")


def _explode_bullet_items(items: list) -> list:
    out = []
    for item in items or []:
        if not isinstance(item, str):
            out.append(item)
            continue
        parts = [part.strip(" -–—") for part in re.split(r"\s*[•●▪◦]\s*", item) if part.strip()]
        if len(parts) > 1:
            out.extend(parts)
        elif item.strip():
            out.append(item.strip())
    return out


def _normalize_section_blocks(blocks: list) -> list:
    by_kind = {}
    order = []
    for item in blocks or []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if kind not in ALLOWED_KINDS:
            continue
        if kind not in by_kind:
            order.append(kind)
        by_kind[kind] = dict(item)
        by_kind[kind]["kind"] = kind
        by_kind[kind]["body"] = str(item.get("body") or "").strip()
        by_kind[kind]["heading"] = str(item.get("heading") or "").strip()
        items = item.get("items") if isinstance(item.get("items"), list) else []
        by_kind[kind]["items"] = _explode_bullet_items(items) if kind in {"benefits", "how_to_use"} else items
        if "source_url" in item:
            by_kind[kind]["source_url"] = item.get("source_url") or ""

    lead_body = (by_kind.get("lead") or {}).get("body") or ""
    about = by_kind.get("about")
    if about:
        about_body, peeled = _peel_usage(about.get("body") or "")
        if lead_body and about_body.startswith(lead_body):
            about_body = about_body[len(lead_body) :].strip()
        about["body"] = about_body
        _attach_usage(by_kind, order, "about", peeled)
        if not about["body"] and not about.get("items"):
            by_kind.pop("about", None)
            order = [kind for kind in order if kind != "about"]

    lead = by_kind.get("lead")
    if lead:
        lead_body, peeled = _peel_usage(lead.get("body") or "")
        lead["body"] = lead_body
        _attach_usage(by_kind, order, "lead", peeled)

    _redistribute_about(by_kind, order)

    return [by_kind[kind] for kind in order if kind in by_kind]


def _sanitize_draft(raw: dict, *, brand_locked: bool) -> dict:
    brand_name = "" if brand_locked else str(raw.get("brand_name") or "").strip()
    blocks = []
    for item in raw.get("blocks") or []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if kind not in ALLOWED_KINDS:
            continue
        source = str(item.get("source_url") or "").strip()
        body = str(item.get("body") or "").strip()
        heading = str(item.get("heading") or "").strip()
        items = item.get("items") if isinstance(item.get("items"), list) else []
        if not _allowed_source(source):
            continue
        if not body and not items:
            continue
        blocks.append(
            {
                "kind": kind,
                "heading": heading,
                "body": body,
                "items": items,
                "source_url": source,
            }
        )
    blocks = _normalize_section_blocks(blocks)
    return {
        "brand_name": brand_name,
        "official_url": str(raw.get("official_url") or "").strip(),
        "notes": str(raw.get("notes") or "").strip(),
        "blocks": blocks,
    }


def ensure_native_brand(name: str) -> ProductBrand | None:
    name = (name or "").strip()
    if not name:
        return None
    found = _lookup_brand(name)
    if found:
        return found
    base = slugify(name, allow_unicode=True) or slugify(name) or "brand"
    slug = base
    suffix = 2
    while ProductBrand.objects.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    brand = ProductBrand.objects.create(slug=slug)
    ProductBrandI18n.objects.create(brand=brand, language="ru", name=name)
    return brand


def save_agent_draft(good: GoodsModel, draft: dict, error: str = "", *, recorded: bool = True) -> ProductContent:
    content, _ = ProductContent.objects.get_or_create(good=good)
    content.agent_draft = draft or None
    content.agent_error = error
    content.agent_run_at = timezone.now() if recorded else None
    content.save(update_fields=["agent_draft", "agent_error", "agent_run_at"])
    return content


def _blocks_from_catalog(good: GoodsModel) -> list:
    parsed = parse_product_description(good.title or "", good.description or "")
    blocks = []
    for item in parsed.get("blocks") or []:
        kind = str(item.get("kind") or "").strip()
        if kind not in ALLOWED_KINDS:
            continue
        body = str(item.get("body") or "").strip()
        items = item.get("items") if isinstance(item.get("items"), list) else []
        if not body and not items:
            continue
        blocks.append(
            {
                "kind": kind,
                "heading": str(item.get("heading") or "").strip(),
                "body": body,
                "items": items,
                "source_url": CATALOG_SOURCE,
            }
        )
    return _normalize_section_blocks(blocks)


def _blocks_from_fetched_pages(pages: list | None) -> list:
    blocks = []
    for url, text in pages or []:
        plain = re.sub(r"\n{3,}", "\n\n", (text or "")).strip()
        if len(plain) < 240:
            continue
        usage = ""
        numbered = re.search(r"(?:^|\n)\s*(1\.\s+[\s\S]+)", plain)
        body = plain
        if numbered:
            body = plain[: numbered.start()].strip()
            usage = numbered.group(1).strip()
        paras = [part.strip() for part in re.split(r"\n\s*\n", body) if len(part.strip()) > 40]
        if paras:
            lead = paras[0]
            sentences = re.split(r"(?<=[.!?])\s+", lead)
            if len(lead) > 320 and len(sentences) > 1:
                lead = sentences[0]
            blocks.append(
                {
                    "kind": "lead",
                    "heading": "",
                    "body": lead,
                    "items": [],
                    "source_url": url,
                }
            )
            about = "\n\n".join(paras[1:] if len(paras) > 1 else paras)
            if about:
                blocks.append(
                    {
                        "kind": "about",
                        "heading": "",
                        "body": about,
                        "items": [],
                        "source_url": url,
                    }
                )
        if usage:
            steps = [part.strip() for part in re.split(r"(?=\d+\.\s+)", usage) if part.strip()]
            blocks.append(
                {
                    "kind": "how_to_use",
                    "heading": "",
                    "body": "" if len(steps) > 1 else usage,
                    "items": steps if len(steps) > 1 else [],
                    "source_url": url,
                }
            )
        break
    return _normalize_section_blocks(blocks)


SECTION_ORDER = (
    "lead",
    "about",
    "benefits",
    "ingredients",
    "texture",
    "how_to_use",
    "suitable_for",
    "volume",
    "weight",
    "set_contents",
    "rest",
)


def _block_chars(block: dict) -> int:
    return len(str(block.get("body") or "")) + len(str(block.get("items") or ""))


def _merge_section_blocks(primary: list, fallback: list) -> list:
    by_kind = {item["kind"]: item for item in fallback if item.get("kind")}
    for item in primary:
        kind = item.get("kind")
        if not kind:
            continue
        existing = by_kind.get(kind)
        if existing and _block_chars(item) < 80 and _block_chars(existing) > 160:
            continue
        by_kind[kind] = item
    return _normalize_section_blocks([by_kind[kind] for kind in SECTION_ORDER if kind in by_kind])


def run_content_agent(good: GoodsModel) -> dict:
    settings = ProductContentAgentSettings.load()
    if not settings.enabled:
        raise AgentConfigError("Агент выключен в админке (Агент контента)")
    pages = _gather_source_pages(good)
    user_payload = _user_payload(good, pages)
    text = call_content_llm(settings.prompt, user_payload, settings.model)
    try:
        raw = extract_json_object(text)
        draft = _sanitize_draft(raw, brand_locked=bool(good.content_brand_id))
    except AgentRunError as extra:
        if "JSON" not in str(extra):
            raise
        draft = {
            "brand_name": "",
            "official_url": "",
            "notes": str(extra),
            "blocks": [],
        }
    catalog_blocks = _blocks_from_catalog(good)
    fetched_blocks = _blocks_from_fetched_pages(pages)
    base = catalog_blocks
    if fetched_blocks:
        base = _merge_section_blocks(fetched_blocks, catalog_blocks)
    if base:
        before = len(draft.get("blocks") or [])
        draft["blocks"] = _merge_section_blocks(draft.get("blocks") or [], base)
        if before == 0:
            extra = "Дополнено текстом официальной страницы и/или описания каталога."
            draft["notes"] = f"{draft.get('notes') or ''} {extra}".strip()
    save_agent_draft(good, draft)
    return draft


def accept_agent_draft(good: GoodsModel) -> int:
    try:
        content = good.pdp_content
    except ProductContent.DoesNotExist as extra:
        raise AgentRunError("Нет карточки контента") from extra
    draft = content.agent_draft
    if not isinstance(draft, dict) or not draft.get("blocks"):
        raise AgentRunError("Нет черновика агента")
    if not good.content_brand_id:
        brand = ensure_native_brand(draft.get("brand_name") or "")
        if brand is not None:
            good.content_brand = brand
            good.save(update_fields=["content_brand"])
    existing = {block.kind: block for block in content.blocks.all()}
    written = 0
    for sort, payload in enumerate(draft["blocks"]):
        block, _ = ProductContentBlock.objects.update_or_create(
            content=content,
            kind=payload["kind"],
            defaults={"sort": 100 + sort},
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
        written += 1
        existing.pop(payload["kind"], None)
    content.agent_draft = None
    content.agent_error = ""
    content.save(update_fields=["agent_draft", "agent_error"])
    refresh_enrichment_from_sections(good)
    return written


def pending_enrichment_queryset():
    return (
        GoodsModel.objects.filter(pdp_content__enrichment_status="needs_enrichment")
        .filter(Q(pdp_content__agent_run_at__isnull=True) | ~Q(pdp_content__agent_error=""))
        .order_by("id")
    )
