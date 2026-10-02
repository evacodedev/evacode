import base64
import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.utils.html import escape, strip_tags

from core.models import Contacts

from .shipping import METHOD_PICKUP

logger = logging.getLogger(__name__)


def _br_order_number(order) -> str:
    return (
        str(getattr(order, "business_ru_order_number", "") or "").strip()
        or str(getattr(order, "business_ru_order_id", "") or "").strip()
    )


def _format_krw(value) -> str:
    try:
        return f"{int(value):,}".replace(",", " ") + " ₩"
    except (TypeError, ValueError):
        return f"{value} ₩"


def _pickup_address() -> str:
    raw = Contacts.objects.values_list("address", flat=True).first() or ""
    text = re.sub(r"<br\s*/?>", "\n", str(raw), flags=re.I)
    return strip_tags(text).strip()


# Те же номера, что в evacode.org/composables/useShopMessengers.js — менять вместе.
SHOP_MESSENGERS = {
    "WhatsApp": [
        ("+7 747 048 3761", "https://wa.me/77470483761"),
        ("+7 777 612 2046", "https://wa.me/77776122046"),
    ],
    "Telegram": [
        ("+7 777 686 8917", "https://t.me/+77776868917"),
    ],
    "Max": [
        ("Открыть чат", "https://max.ru/u/f9LHodD0cOIQhBBIhcEfdYTRxN1PLhQ-9BSSX1tnitJ9JPdcvqLdsj67dwU"),
    ],
}


def _shop_contacts() -> dict:
    row = (
        Contacts.objects.values("phone", "email", "instagram", "tiktok", "facebook", "address").first()
        or {}
    )
    return {key: str(value or "").strip() for key, value in row.items()}


def _contact_rows(contacts: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    rows = []
    phone = contacts.get("phone", "")
    if phone:
        rows.append(("Телефон", [(phone, "tel:+" + re.sub(r"\D", "", phone))]))
    rows.extend(SHOP_MESSENGERS.items())
    email = contacts.get("email") or ORDER_HELP_EMAIL
    rows.append(("Email", [(email, f"mailto:{email}")]))
    socials = [
        (name, contacts.get(key, ""))
        for name, key in (("Instagram", "instagram"), ("TikTok", "tiktok"), ("Facebook", "facebook"))
        if contacts.get(key)
    ]
    if socials:
        rows.append(("Соцсети", socials))
    return rows


def _contacts_text(contacts: dict) -> list[str]:
    lines = ["Связаться с нами:"]
    for label, links in _contact_rows(contacts):
        if label == "Max":
            lines.append(f"Max: {links[0][1]}")
        elif label == "Соцсети":
            lines.extend(f"{name}: {href}" for name, href in links)
        else:
            lines.append(f"{label}: {', '.join(text for text, _href in links)}")
    address = _plain_address(contacts.get("address", ""))
    if address:
        lines.append(f"Офис в Корее: {address}")
    return lines


def _plain_address(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", ", ", str(raw or ""), flags=re.I)
    return strip_tags(text).strip()


def _contacts_html(contacts: dict) -> str:
    rows = []
    for label, links in _contact_rows(contacts):
        anchors = " &nbsp;·&nbsp; ".join(
            f'<a href="{escape(href)}" style="color:#1A1917;text-decoration:none;border-bottom:1px solid #B89254;">'
            f"{escape(text)}</a>"
            for text, href in links
        )
        rows.append(
            f'<tr><td width="96" style="padding:6px 0;font-size:13px;color:#8A8680;vertical-align:top;">{escape(label)}</td>'
            f'<td style="padding:6px 0;font-size:14px;line-height:1.6;color:#1A1917;">{anchors}</td></tr>'
        )
    address = _plain_address(contacts.get("address", ""))
    if address:
        rows.append(
            f'<tr><td width="96" style="padding:6px 0;font-size:13px;color:#8A8680;vertical-align:top;">Офис</td>'
            f'<td style="padding:6px 0;font-size:13px;line-height:1.5;color:#1A1917;">{escape(address)}<br>'
            f'<span style="color:#8A8680;">Ансан, провинция Кёнгидо, Южная Корея</span></td></tr>'
        )
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="margin:28px 0 0;background:#F7F4EF;border-radius:8px;">'
        '<tr><td style="padding:20px 22px;">'
        '<p style="margin:0 0 4px;font-size:15px;font-weight:700;color:#1A1917;">Связаться с нами</p>'
        '<p style="margin:0 0 12px;font-size:13px;line-height:1.5;color:#8A8680;">'
        "Консультанты ответят на вопросы о заказе и уходе — пишите в любой удобный мессенджер.</p>"
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0">'
        f'{"".join(rows)}</table></td></tr></table>'
    )


def _address_html(text: str) -> str:
    return "<br>".join(escape(line) for line in text.splitlines() if line.strip())


ORDER_HELP_EMAIL = "orders@evacode.co.kr"
BR_CDN_PREFIX = "https://a46291.business.ru/"
TRACKING_URL = "https://t.17track.net/ru#nums={number}"
TRACKING_NUMBER_RE = re.compile(r"^[A-Z0-9-]{6,40}$")

# Цвета витрины (правило evacode-ui): тёплый белый, текст, вторичный, золото.
_BG = "#F7F4EF"
_INK = "#1A1917"
_MUTED = "#8A8680"
_GOLD = "#B89254"
_LINE = "#E8E4DE"

STAGE_PAID = 0
STAGE_ACCEPTED = 1
STAGE_SHIPPED = 2


class OrderEmailError(Exception):
    """Письмо клиенту нельзя отправить: текст ошибки показываем в админке."""


def _site_url() -> str:
    base = str(getattr(settings, "FRONTEND_PUBLIC_URL", "") or "").strip().rstrip("/")
    return base or "https://evacode.co.kr"


def _email_image_url(source: str) -> str:
    url = re.sub(r"^http://a46291\.business\.ru", "https://a46291.business.ru", str(source or ""), flags=re.I)
    if not url.startswith(BR_CDN_PREFIX):
        return url
    encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    # JPEG, а не WebP: Outlook и часть почтовых клиентов WebP не показывают.
    return f"{_site_url()}/img/insecure/rs:fit:128:128/q:80/f:jpg/{encoded}"


def _item_image(item) -> str:
    good = getattr(item, "good", None)
    if good is None:
        return ""
    image = good.images.order_by("sort", "id").first()
    return _email_image_url(image.url) if image else ""


def _order_items(order) -> list:
    items = order.items.all()
    if hasattr(items, "select_related"):
        items = items.select_related("good")
    return list(items)


def _delivery_address(order) -> str:
    return ", ".join(part for part in [order.postal_code, order.country, order.city, order.address] if part)


def tracking_url(number: str) -> str:
    return TRACKING_URL.format(number=number)


def normalize_tracking_number(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def _stage_labels(is_pickup: bool) -> tuple[str, str, str]:
    return ("Оплачен", "В обработке", "Можно забрать" if is_pickup else "Отправлен")


def _client_email_copy(order, stage: int, br_number: str, tracking_number: str = "") -> dict:
    is_pickup = order.shipping_method == METHOD_PICKUP
    number = br_number or str(order.public_id)
    if stage == STAGE_SHIPPED:
        return {
            "subject": f"Evacode — заказ {number} отправлен, трек-номер {tracking_number}",
            "title": "Заказ отправлен",
            "lead": (
                "Посылка передана в EMS Korea Post. Отследить её можно по трек-номеру ниже — "
                "статус обычно появляется в течение суток после отправки."
            ),
        }
    if stage == STAGE_ACCEPTED:
        next_step = (
            "Когда заказ будет готов к выдаче, мы напишем."
            if is_pickup
            else "Когда передадим посылку в EMS, пришлём письмо с трек-номером."
        )
        return {
            "subject": f"Evacode — заказ {number} принят в обработку",
            "title": "Заказ принят в обработку",
            "lead": f"Мы проверили заказ и начали его собирать. {next_step}",
        }
    return {
        "subject": f"Evacode — заказ {number} оплачен",
        "title": "Заказ оплачен",
        "lead": (
            "Спасибо за покупку! Оплата прошла, заказ ждёт подтверждения: "
            "мы проверим товары и напишем, как только возьмём его в работу."
        ),
    }


def _stages_html(stage: int, is_pickup: bool) -> str:
    cells = []
    for index, label in enumerate(_stage_labels(is_pickup)):
        reached = index <= stage
        bar = _GOLD if reached else _LINE
        color = _INK if index == stage else (_GOLD if reached else _MUTED)
        weight = "700" if index == stage else "400"
        mark = "✓ " if index < stage else ""
        cells.append(
            f'<td width="33%" style="padding:0 4px;vertical-align:top;">'
            f'<div style="height:4px;border-radius:2px;background:{bar};font-size:0;line-height:0;">&nbsp;</div>'
            f'<p style="margin:8px 0 0;font-size:12px;line-height:1.3;color:{color};font-weight:{weight};">'
            f"{mark}{escape(label)}</p></td>"
        )
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 28px;">'
        f'<tr>{"".join(cells)}</tr></table>'
    )


def _items_html(items) -> str:
    rows = []
    for item in items:
        image = _item_image(item)
        thumb = (
            f'<img src="{escape(image)}" width="64" height="64" alt="" '
            f'style="display:block;width:64px;height:64px;object-fit:contain;border-radius:6px;background:{_BG};">'
            if image
            else f'<div style="width:64px;height:64px;border-radius:6px;background:{_BG};"></div>'
        )
        rows.append(
            "<tr>"
            f'<td width="76" style="padding:12px 0;border-bottom:1px solid {_LINE};vertical-align:middle;">{thumb}</td>'
            f'<td style="padding:12px 12px 12px 0;border-bottom:1px solid {_LINE};vertical-align:middle;'
            f'font-size:14px;line-height:1.4;color:{_INK};">{escape(item.title)}'
            f'<div style="margin-top:4px;font-size:13px;color:{_MUTED};">'
            f"{item.quantity} шт × {escape(_format_krw(item.price_krw))}</div></td>"
            f'<td align="right" style="padding:12px 0;border-bottom:1px solid {_LINE};vertical-align:middle;'
            f'font-size:14px;font-weight:600;white-space:nowrap;color:{_INK};">'
            f"{escape(_format_krw(item.line_total_krw))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _totals_html(order, is_pickup: bool) -> str:
    shipping = "Самовывоз" if is_pickup else _format_krw(order.shipping_krw or 0)
    goods = order.goods_krw or max(int(order.amount_krw or 0) - int(order.shipping_krw or 0), 0)

    def row(label, value, strong=False):
        size = "16px" if strong else "14px"
        weight = "700" if strong else "400"
        color = _INK if strong else _MUTED
        return (
            f'<tr><td style="padding:6px 0;font-size:{size};font-weight:{weight};color:{color};">{escape(label)}</td>'
            f'<td align="right" style="padding:6px 0;font-size:{size};font-weight:{weight};color:{_INK};">{value}</td></tr>'
        )

    approx = _approx_total(order)
    total = escape(_format_krw(order.amount_krw))
    if approx:
        total += f'<div style="font-size:12px;font-weight:400;color:{_MUTED};">≈ {escape(approx)}</div>'
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:8px 0 28px;">'
        + row("Товары", escape(_format_krw(goods)))
        + row("Доставка EMS" if not is_pickup else "Получение", escape(shipping))
        + row("Итого", total, strong=True)
        + "</table>"
    )


def _delivery_html(order, is_pickup: bool, br_number: str, stage: int) -> str:
    title_style = f"margin:0 0 10px;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:{_MUTED};"
    text_style = f"margin:0 0 4px;font-size:14px;line-height:1.5;color:{_INK};"
    if is_pickup:
        pickup = _pickup_address()
        parts = [f'<p style="{title_style}">Самовывоз в Корее</p>']
        if pickup:
            parts.append(f'<p style="{text_style}">{_address_html(pickup)}</p>')
        if br_number:
            parts.append(
                f'<p style="margin:10px 0 0;font-size:13px;line-height:1.5;color:{_MUTED};">'
                f"При получении назовите номер заказа <strong style=\"color:{_INK};\">{escape(br_number)}</strong>.</p>"
            )
    else:
        parts = [
            f'<p style="{title_style}">Доставим EMS по адресу</p>',
            f'<p style="{text_style}font-weight:600;">{escape(order.first_name)}</p>',
            f'<p style="{text_style}">{escape(_delivery_address(order))}</p>',
        ]
        if order.phone:
            parts.append(f'<p style="margin:0;font-size:13px;color:{_MUTED};">{escape(order.phone)}</p>')
        if stage < STAGE_SHIPPED:
            parts.append(
                f'<p style="margin:10px 0 0;font-size:13px;line-height:1.5;color:{_MUTED};">'
                f"Если в адресе ошибка — просто ответьте на это письмо, пока заказ не отправлен.</p>"
            )
    return (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        f'style="margin:0 0 28px;border:1px solid {_LINE};border-radius:8px;">'
        f'<tr><td style="padding:18px 20px;">{"".join(parts)}</td></tr></table>'
    )


def _tracking_html(tracking_number: str) -> str:
    link = escape(tracking_url(tracking_number))
    return (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        f'style="margin:0 0 28px;background:{_INK};border-radius:8px;">'
        '<tr><td align="center" style="padding:24px 20px;">'
        f'<p style="margin:0 0 8px;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:{_GOLD};">'
        "Трек-номер EMS</p>"
        f'<p style="margin:0 0 18px;font-size:24px;font-weight:700;letter-spacing:0.08em;color:#FFFFFF;'
        f'font-family:Menlo,Consolas,monospace;">{escape(tracking_number)}</p>'
        f'<a href="{link}" style="display:inline-block;padding:12px 28px;border-radius:6px;background:{_GOLD};'
        'color:#FFFFFF;font-size:14px;font-weight:600;text-decoration:none;">Отследить посылку</a>'
        "</td></tr></table>"
    )


def _payment_method(order) -> str:
    return "через консультанта" if getattr(order, "consultant_id", None) else "PayPal"


def _approx_total(order) -> str:
    """Сумма во второй валюте: у PayPal — USD, у консультанта — валюта, показанная клиенту."""
    if getattr(order, "consultant_id", None):
        currency = (getattr(order, "display_currency", "") or "").upper()
        amount = getattr(order, "display_amount", None)
        if currency and currency != "KRW" and amount is not None:
            return f"{amount} {currency}"
        return ""
    return f"{order.amount_usd} USD"


def build_client_email(order, stage: int, tracking_number: str = "") -> tuple[str, str, str]:
    """(subject, text, html) письма клиенту о статусе заказа."""
    br_number = _br_order_number(order)
    number = br_number or str(order.public_id)
    items = _order_items(order)
    is_pickup = order.shipping_method == METHOD_PICKUP
    copy = _client_email_copy(order, stage, br_number, tracking_number)
    contacts = _shop_contacts()
    site = _site_url()
    paid_at = timezone.localtime(order.paid_at).strftime("%d.%m.%Y") if getattr(order, "paid_at", None) else ""
    goods = order.goods_krw or max(int(order.amount_krw or 0) - int(order.shipping_krw or 0), 0)

    lines = [f"Здравствуйте, {order.first_name}!", "", copy["title"], copy["lead"], ""]
    if stage == STAGE_SHIPPED and tracking_number:
        lines += [f"Трек-номер EMS: {tracking_number}", f"Отследить: {tracking_url(tracking_number)}", ""]
    lines += [
        f"Номер заказа: {number}",
        f"Оплата: прошла ({_payment_method(order)})",
        "",
        "Состав заказа:",
    ]
    for item in items:
        lines.append(
            f"• {item.title} — {item.quantity} шт × {_format_krw(item.price_krw)} = {_format_krw(item.line_total_krw)}"
        )
    lines += [
        "",
        f"Товары: {_format_krw(goods)}",
        "Получение: самовывоз" if is_pickup else f"Доставка EMS: {_format_krw(order.shipping_krw or 0)}",
        f"Итого: {_format_krw(order.amount_krw)}" + (f" (≈ {_approx_total(order)})" if _approx_total(order) else ""),
        "",
    ]
    if is_pickup:
        pickup = _pickup_address()
        lines.append("Самовывоз в Корее")
        if pickup:
            lines.append(pickup)
        if br_number:
            lines.append(f"При получении назовите номер заказа {br_number}.")
    else:
        lines += ["Доставим EMS по адресу:", order.first_name, _delivery_address(order)]
        if order.phone:
            lines.append(order.phone)
    lines += ["", f"Мои заказы: {site}/account", ""]
    lines += _contacts_text(contacts)
    lines += ["Или просто ответьте на это письмо.", "", "Evacode · Korean beauty from Seoul", site]
    text = "\n".join(lines)

    meta = f"Заказ № {escape(number)}"
    if paid_at:
        meta += f" · {paid_at}"
    tracking_block = _tracking_html(tracking_number) if stage == STAGE_SHIPPED and tracking_number else ""
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(copy["title"])}</title></head>
<body style="margin:0;padding:0;background:{_BG};">
  <div style="display:none;max-height:0;overflow:hidden;">{escape(copy["lead"])}</div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{_BG};padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;font-family:Inter,Lato,Arial,sans-serif;color:{_INK};">
          <tr>
            <td align="center" style="background:{_INK};border-radius:10px 10px 0 0;padding:28px 24px 24px;">
              <p style="margin:0;font-size:22px;font-weight:700;letter-spacing:0.36em;color:{_GOLD};">EVACODE</p>
              <p style="margin:6px 0 0;font-size:11px;letter-spacing:0.24em;text-transform:uppercase;color:#CFC8BD;">Korean beauty · Seoul</p>
            </td>
          </tr>
          <tr>
            <td style="height:3px;background:{_GOLD};font-size:0;line-height:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="background:#FFFFFF;border-radius:0 0 10px 10px;padding:36px 32px 32px;">
              <p style="margin:0 0 8px;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:{_MUTED};">{meta}</p>
              <h1 style="margin:0 0 14px;font-size:26px;font-weight:700;line-height:1.25;color:{_INK};">{escape(copy["title"])}</h1>
              <p style="margin:0 0 6px;font-size:15px;line-height:1.55;">Здравствуйте, {escape(order.first_name)}!</p>
              <p style="margin:0 0 20px;font-size:15px;line-height:1.55;color:#4A4743;">{escape(copy["lead"])}</p>
              <p style="margin:0 0 28px;">
                <span style="display:inline-block;padding:7px 14px;border-radius:999px;background:#EAF3EC;color:#2F6B3A;font-size:13px;font-weight:600;">✓ Оплата прошла · {escape(_payment_method(order))}</span>
              </p>
              {_stages_html(stage, is_pickup)}
              {tracking_block}
              <p style="margin:0 0 4px;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:{_MUTED};">Ваш заказ</p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                {_items_html(items)}
              </table>
              {_totals_html(order, is_pickup)}
              {_delivery_html(order, is_pickup, br_number, stage)}
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="center" style="padding:4px 0 8px;">
                    <a href="{escape(site)}/account" style="display:inline-block;padding:12px 28px;border-radius:6px;border:1px solid {_INK};color:{_INK};font-size:14px;font-weight:600;text-decoration:none;">Мои заказы</a>
                  </td>
                </tr>
              </table>
              {_contacts_html(contacts)}
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:22px 16px 0;font-size:12px;line-height:1.6;color:{_MUTED};">
              Можно просто ответить на это письмо — оно придёт нам на {ORDER_HELP_EMAIL}.<br>
              Evacode · Korean beauty from Seoul · <a href="{escape(site)}" style="color:{_GOLD};text-decoration:none;">evacode.co.kr</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return copy["subject"], text, html


def build_order_confirmation_bodies(order) -> tuple[str, str]:
    _subject, text, html = build_client_email(order, STAGE_PAID)
    return text, html


def _local_dt(value) -> str:
    if not value:
        return "—"
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")


def _value(value) -> str:
    text = str(value or "").strip()
    return text or "—"


def build_order_help_body(order, user, phone: str, message: str) -> str:
    br_number = _br_order_number(order)
    items = list(order.items.all())
    account_name = (user.get_full_name() or "").strip() or user.username
    account_email = (user.email or user.username or "").strip()
    address = ", ".join(
        part for part in [order.postal_code, order.country, order.city, order.address] if part
    )
    if order.shipping_method == METHOD_PICKUP:
        shipping = "Самовывоз"
    else:
        destination = order.country or order.shipping_destination or ""
        shipping = f"EMS{f' ({destination})' if destination else ''}"
    admin_url = (
        f"{str(settings.BACKEND_PUBLIC_URL or '').rstrip('/')}/admin/market/siteorder/{order.pk}/change/"
    )

    lines = [
        "ВОПРОС КЛИЕНТА",
        message,
        "",
        "КЛИЕНТ",
        f"Имя в аккаунте: {_value(account_name)}",
        f"Email аккаунта: {_value(account_email)}",
        f"Телефон для связи (из формы): {_value(phone)}",
        f"Телефон в заказе: {_value(order.phone)}",
        f"ID пользователя на сайте: {user.pk}",
        "",
        "ЗАКАЗ",
        f"Номер Business.Ru: {_value(br_number)}",
        f"Код заказа на сайте: {order.public_id}",
        f"Статус: {order.get_status_display()}",
        f"Создан: {_local_dt(order.created_at)}",
        f"Оплачен: {_local_dt(order.paid_at)}",
        f"Получатель: {_value(order.first_name)}, {_value(order.phone)}, {_value(order.email)}",
        f"Получение: {shipping}",
        f"Адрес: {_value(address)}",
        f"Комментарий к заказу: {_value(order.comment)}",
        "",
        "СОСТАВ",
    ]
    for item in items:
        lines.append(
            f"• {item.title} (ID товара {item.good_id_snapshot}) — {item.quantity} шт × "
            f"{_format_krw(item.price_krw)} = {_format_krw(item.line_total_krw)}"
        )
    if not items:
        lines.append("—")
    lines.extend(
        [
            f"Товары: {_format_krw(order.goods_krw)}",
            f"Доставка: {_format_krw(order.shipping_krw)}",
            f"Итого: {_format_krw(order.amount_krw)} ({order.amount_usd} USD)",
            f"Вес: {f'{order.weight_grams} г' if order.weight_grams else '—'}",
            "",
            "ОПЛАТА PAYPAL",
            f"Режим: {_value(order.paypal_mode)}",
            f"PayPal order: {_value(order.paypal_order_id)}",
            f"Capture: {_value(order.paypal_capture_id)}",
            f"Чек: {_value(order.paypal_receipt_url)}",
            "",
            "BUSINESS.RU",
            f"Заказ покупателя: {_value(order.business_ru_order_number)} (id {_value(order.business_ru_order_id)})",
            f"Входящая оплата: {_value(order.business_ru_payment_number)}",
            f"Резерв: {_value(order.business_ru_reservation_number)}",
            f"Ошибка выгрузки: {_value(order.business_ru_error)}",
            f"Письмо клиенту отправлено: {_local_dt(order.confirmation_email_sent_at)}",
            "",
            f"Заказ в админке: {admin_url}",
            f"Обращение из личного кабинета, {_local_dt(timezone.now())} (Сеул).",
            "Ответ на это письмо уйдёт клиенту.",
        ]
    )
    return "\n".join(lines)


def send_order_help_email(order, user, phone: str, message: str) -> None:
    br_number = _br_order_number(order)
    account_email = (user.email or "").strip() or (order.email or "").strip()
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or settings.EMAIL_HOST_USER
    EmailMultiAlternatives(
        subject=f"Помощь клиенту — заказ {br_number or order.public_id}",
        body=build_order_help_body(order, user, phone, message),
        from_email=from_email,
        to=[ORDER_HELP_EMAIL],
        reply_to=[account_email] if account_email else None,
    ).send(fail_silently=False)


def send_order_confirmation_email(order, *, force: bool = False) -> bool:
    if order.status != order.Status.PAID:
        return False
    if getattr(order, "confirmation_email_sent_at", None) and not force:
        return False
    br_number = _br_order_number(order)
    if not br_number:
        logger.warning("Письмо заказа %s не отправлено: нет номера Business.Ru", order.public_id)
        return False
    if not (getattr(settings, "EMAIL_HOST_USER", "") or "").strip():
        logger.warning("Письмо заказа %s не отправлено: не настроен EMAIL_HOST_USER", order.public_id)
        return False
    if not (order.email or "").strip():
        return False

    subject, text, html = build_client_email(order, STAGE_PAID)
    try:
        _send_to_client(order, subject, text, html)
    except Exception:
        logger.exception("Не удалось отправить письмо по заказу %s", order.public_id)
        return False

    order.confirmation_email_sent_at = timezone.now()
    order.save(update_fields=["confirmation_email_sent_at", "updated_at"])
    return True


def status_email_test_to() -> str:
    return str(getattr(settings, "ORDER_STATUS_EMAIL_TEST_TO", "") or "").strip()


def status_email_recipient(order) -> str:
    return status_email_test_to() or (order.email or "").strip()


def _send_to_client(order, subject: str, text: str, html: str, to: str = "") -> None:
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or settings.EMAIL_HOST_USER
    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=from_email,
        to=[to or order.email.strip()],
        reply_to=[ORDER_HELP_EMAIL],
    )
    message.attach_alternative(html, "text/html")
    message.send(fail_silently=False)


def _check_client_email(order) -> None:
    if order.status != order.Status.PAID:
        raise OrderEmailError("письмо клиенту — только для оплаченного заказа")
    if not (order.email or "").strip():
        raise OrderEmailError("в заказе нет email клиента")
    if not (getattr(settings, "EMAIL_HOST_USER", "") or "").strip():
        raise OrderEmailError("почта не настроена (EMAIL_HOST_USER)")


def _send_status_email(order, subject: str, text: str, html: str) -> str:
    to = status_email_recipient(order)
    if status_email_test_to():
        subject = f"[ТЕСТ, клиент: {order.email}] {subject}"
    _send_to_client(order, subject, text, html, to=to)
    return to


def send_order_accepted_email(order) -> str:
    """«Заказ принят в обработку» — по кнопке «Подтвердить получение» в админке. Возвращает адрес получателя."""
    _check_client_email(order)
    subject, text, html = build_client_email(order, STAGE_ACCEPTED)
    to = _send_status_email(order, subject, text, html)
    order.accepted_email_sent_at = timezone.now()
    order.save(update_fields=["accepted_email_sent_at", "updated_at"])
    return to


def send_order_tracking_email(order, tracking_number: str) -> str:
    """Письмо с трек-номером EMS. Возвращает сохранённый номер."""
    number = normalize_tracking_number(tracking_number)
    if order.shipping_method == METHOD_PICKUP:
        raise OrderEmailError("это самовывоз — трек-номер не нужен")
    if not number:
        raise OrderEmailError("введите трек-номер")
    if not TRACKING_NUMBER_RE.match(number):
        raise OrderEmailError("проверьте трек-номер: только латиница и цифры, например EG123456789KR")
    _check_client_email(order)
    subject, text, html = build_client_email(order, STAGE_SHIPPED, tracking_number=number)
    _send_status_email(order, subject, text, html)
    order.tracking_number = number
    order.tracking_email_sent_at = timezone.now()
    order.save(update_fields=["tracking_number", "tracking_email_sent_at", "updated_at"])
    return number
