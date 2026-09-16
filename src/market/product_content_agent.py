from __future__ import annotations

import json
import os
import re

import requests
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
from .product_content import _lookup_brand
from .product_content_prompt import BRAND_SITE_RULES, DEFAULT_AGENT_PROMPT, official_site_for_text

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
    try:
        data = json.loads(blob, strict=False)
    except json.JSONDecodeError:
        try:
            data = json.loads(_repair_json(blob), strict=False)
        except json.JSONDecodeError as extra:
            snippet = blob[max(0, extra.pos - 80) : extra.pos + 80] if extra.pos is not None else blob[:160]
            raise AgentRunError(
                f"Некорректный JSON от модели: {extra}. Фрагмент: {snippet!r}"
            ) from extra
    if not isinstance(data, dict):
        raise AgentRunError("JSON агента должен быть объектом")
    return data


def _repair_json(blob: str) -> str:
    fixed = (
        blob.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )
    return re.sub(r",(\s*[}\]])", r"\1", fixed)


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


def _user_payload(good: GoodsModel) -> str:
    brand = ""
    if good.content_brand_id:
        brand = str(good.content_brand)
    hint = official_site_for_text(f"{good.title} {brand}")
    official_line = (
        f"preferred_official_url: {hint}\n"
        "Ищи этот товар на этом сайте. Hwahae / Olive Young / Coupang — не основной источник.\n"
        if hint
        else ""
    )
    return (
        f"id: {good.id}\n"
        f"title: {good.title}\n"
        f"brand_already_set: {brand or '(пусто — можно предложить каноническое имя)'}\n"
        f"kind: {good.content_kind or ''}\n"
        f"weight_grams_from_catalog: {good.weight}\n"
        f"{official_line}"
        f"description_from_BR:\n{good.description or ''}\n"
    )


USAGE_SPLIT_RE = re.compile(
    r"(?:^|\n)\s*(Способ\s+(?:использования|применения)[\s\S]*)",
    re.IGNORECASE,
)
USAGE_STEP_RE = re.compile(r"(?=Способ\s+использования\s+\d)", re.IGNORECASE)


def _peel_usage(body: str) -> tuple[str, str]:
    text = (body or "").strip()
    match = USAGE_SPLIT_RE.search(text)
    if not match:
        return text, ""
    return text[: match.start()].strip(), match.group(1).strip()


def _usage_items(text: str) -> list:
    chunks = [part.strip() for part in USAGE_STEP_RE.split(text or "") if part.strip()]
    return chunks if len(chunks) > 1 else []


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
        by_kind[kind]["items"] = items
        if "source_url" in item:
            by_kind[kind]["source_url"] = item.get("source_url") or ""

    lead_body = (by_kind.get("lead") or {}).get("body") or ""
    about = by_kind.get("about")
    if about:
        about_body, peeled = _peel_usage(about.get("body") or "")
        if lead_body and about_body.startswith(lead_body):
            about_body = about_body[len(lead_body) :].strip()
        about["body"] = about_body
        if peeled:
            usage = by_kind.get("how_to_use") or {"kind": "how_to_use", "heading": "", "body": "", "items": []}
            if not usage.get("body") and not usage.get("items"):
                steps = _usage_items(peeled)
                usage["body"] = "" if steps else peeled
                usage["items"] = steps or usage.get("items") or []
                usage["source_url"] = usage.get("source_url") or about.get("source_url") or ""
                by_kind["how_to_use"] = usage
                if "how_to_use" not in order:
                    order.append("how_to_use")
        if not about["body"] and not about.get("items"):
            by_kind.pop("about", None)
            order = [kind for kind in order if kind != "about"]

    lead = by_kind.get("lead")
    if lead:
        lead_body, peeled = _peel_usage(lead.get("body") or "")
        lead["body"] = lead_body
        if peeled and "how_to_use" not in by_kind:
            steps = _usage_items(peeled)
            by_kind["how_to_use"] = {
                "kind": "how_to_use",
                "heading": "",
                "body": "" if steps else peeled,
                "items": steps,
                "source_url": lead.get("source_url") or "",
            }
            order.append("how_to_use")

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
        if not source:
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


def save_agent_draft(good: GoodsModel, draft: dict, error: str = "") -> ProductContent:
    content, _ = ProductContent.objects.get_or_create(good=good)
    content.agent_draft = draft or None
    content.agent_error = error
    content.agent_run_at = timezone.now()
    content.save(update_fields=["agent_draft", "agent_error", "agent_run_at"])
    return content


def run_content_agent(good: GoodsModel) -> dict:
    settings = ProductContentAgentSettings.load()
    if not settings.enabled:
        raise AgentConfigError("Агент выключен в админке (Агент контента)")
    user_payload = _user_payload(good)
    text = call_content_llm(settings.prompt, user_payload, settings.model)
    raw = extract_json_object(text)
    draft = _sanitize_draft(raw, brand_locked=bool(good.content_brand_id))
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
    content.agent_error = ""
    content.save(update_fields=["agent_error"])
    return written


def pending_enrichment_queryset():
    return GoodsModel.objects.filter(
        pdp_content__enrichment_status="needs_enrichment",
        pdp_content__agent_run_at__isnull=True,
    ).order_by("id")
