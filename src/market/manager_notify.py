import logging
import os
import time

import requests
from django.conf import settings
from django.core.mail import EmailMessage

from .order_email import ORDER_HELP_EMAIL

logger = logging.getLogger(__name__)

TELEGRAM_TEXT_LIMIT = 4096
# С VPS часть запросов к Telegram зависает: держим сумму попыток заметно ниже таймаута gunicorn (60 с).
TELEGRAM_TIMEOUT = (3, 5)
TELEGRAM_ATTEMPTS = 3
# callback "handle" обрабатывает tg_bot: дописывает «Обработано: @ник» и убирает кнопку.
HANDLE_KEYBOARD = {"inline_keyboard": [[{"text": "ОБРАБОТАТЬ✅", "callback_data": "handle"}]]}


def _telegram_chat_ids() -> list[str]:
    """Группа из CHAT_ID — основная. TELEGRAM_EXTRA_CHAT_ID — копия в @Evacode_83, через запятую."""
    primary = (os.getenv("CHAT_ID") or "").strip()
    ids: list[str] = []
    if primary:
        ids.append(primary)
    extra = os.getenv("TELEGRAM_EXTRA_CHAT_ID") or ""
    for part in extra.split(","):
        chat_id = part.strip()
        if chat_id and chat_id not in ids:
            ids.append(chat_id)
    return ids


def _post_telegram(token: str, chat_id: str, text: str, *, attempts: int) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:TELEGRAM_TEXT_LIMIT],
        "reply_markup": HANDLE_KEYBOARD,
    }
    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(url, json=payload, timeout=TELEGRAM_TIMEOUT)
            if response.ok and response.json().get("ok"):
                return True
            logger.warning(
                "Telegram чат %s ответил %s на попытке %s: %s",
                chat_id,
                response.status_code,
                attempt,
                response.text[:300],
            )
            if 400 <= response.status_code < 500 and response.status_code != 429:
                return False
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Telegram чат %s недоступен на попытке %s: %s", chat_id, attempt, exc)
        if attempt < attempts:
            time.sleep(0.5 * attempt)
    return False


def send_telegram(text: str) -> bool:
    token = (os.getenv("BOT_TOKEN") or "").strip()
    chat_ids = _telegram_chat_ids()
    if not token or not chat_ids:
        logger.warning("Telegram не настроен: нет BOT_TOKEN или CHAT_ID")
        return False
    # Успех заявки решает группа. Дополнительные чаты — копия, их сбой не гасит основную отправку.
    primary_ok = _post_telegram(token, chat_ids[0], text, attempts=TELEGRAM_ATTEMPTS)
    for chat_id in chat_ids[1:]:
        if not _post_telegram(token, chat_id, text, attempts=1):
            logger.warning("Telegram копия не ушла в дополнительный чат %s", chat_id)
    return primary_ok


def send_managers_email(subject: str, text: str, reply_to: str = "") -> bool:
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or settings.EMAIL_HOST_USER
    reply = (reply_to or "").strip()
    try:
        EmailMessage(
            subject=subject,
            body=text,
            from_email=from_email,
            to=[ORDER_HELP_EMAIL],
            reply_to=[reply] if reply else None,
        ).send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Письмо менеджерам «%s» не отправлено", subject)
        return False


def notify_managers(text: str, *, subject: str, reply_to: str = "") -> bool:
    if send_telegram(text):
        return True
    logger.warning("Telegram не принял «%s», отправляем на %s", subject, ORDER_HELP_EMAIL)
    return send_managers_email(subject, f"{text}\n\n(Telegram недоступен, копия письмом.)", reply_to)
