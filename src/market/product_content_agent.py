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
from .product_content_prompt import DEFAULT_AGENT_PROMPT

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


def extract_json_object(text: str) -> dict:
    raw = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fenced:
        raw = fenced.group(1)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise AgentRunError("Модель не вернула JSON")
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as extra:
        raise AgentRunError(f"Некорректный JSON от модели: {extra}") from extra
    if not isinstance(data, dict):
        raise AgentRunError("JSON агента должен быть объектом")
    return data


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
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or "gpt-4.1-mini",
            "tools": [{"type": "web_search"}],
            "input": [
                {"role": "developer", "content": system_prompt or DEFAULT_AGENT_PROMPT},
                {"role": "user", "content": user_payload},
            ],
        },
        timeout=180,
    )
    if response.status_code >= 400:
        raise AgentRunError(f"OpenAI {response.status_code}: {response.text[:500]}")
    data = response.json()
    text = _output_text(data)
    if not text.strip():
        raise AgentRunError("Пустой ответ модели")
    return text


def _user_payload(good: GoodsModel) -> str:
    brand = ""
    if good.content_brand_id:
        brand = str(good.content_brand)
    return (
        f"id: {good.id}\n"
        f"title: {good.title}\n"
        f"brand_already_set: {brand or '(пусто — можно предложить каноническое имя)'}\n"
        f"kind: {good.content_kind or ''}\n"
        f"weight_grams_from_catalog: {good.weight}\n"
        f"description_from_BR:\n{good.description or ''}\n"
    )


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
