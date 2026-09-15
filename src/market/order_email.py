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


def _address_html(text: str) -> str:
    return "<br>".join(escape(line) for line in text.splitlines() if line.strip())


def build_order_confirmation_bodies(order) -> tuple[str, str]:
    br_number = _br_order_number(order)
    items = list(order.items.all())
    is_pickup = order.shipping_method == METHOD_PICKUP
    pickup = _pickup_address()

    lines = [
        f"Здравствуйте, {order.first_name}!",
        "",
        "Ваш заказ на evacode.org оплачен.",
        f"Номер заказа: {br_number}" if br_number else "Номер заказа уточняется.",
        f"Сумма: {_format_krw(order.amount_krw)} ({order.amount_usd} USD)",
        "",
        "Состав заказа:",
    ]
    for item in items:
        lines.append(
            f"• {item.title} — {item.quantity} шт × {_format_krw(item.price_krw)} "
            f"= {_format_krw(item.line_total_krw)}"
        )
    lines.append("")
    if is_pickup:
        lines.append("Самовывоз")
        if pickup:
            lines.append(pickup)
        if br_number:
            lines.append(
                f"Заберите заказ, предъявив номер заказа {br_number}."
            )
    else:
        destination = order.country or order.shipping_destination or ""
        lines.append(f"Доставка EMS{f' ({destination})' if destination else ''}")
        if order.shipping_krw:
            lines.append(f"Стоимость доставки: {_format_krw(order.shipping_krw)}")
        address = ", ".join(
            part
            for part in [
                order.postal_code,
                order.country,
                order.city,
                order.address,
            ]
            if part
        )
        if address:
            lines.append(f"Адрес: {address}")
    lines.extend(["", "Спасибо за покупку!", "Evacode", "https://www.evacode.org"])
    text = "\n".join(lines)

    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td style=\"padding:10px 0;border-bottom:1px solid #E8E4DE;\">{escape(item.title)}</td>"
            f"<td style=\"padding:10px 0;border-bottom:1px solid #E8E4DE;text-align:center;\">{item.quantity}</td>"
            f"<td style=\"padding:10px 0;border-bottom:1px solid #E8E4DE;text-align:right;\">"
            f"{escape(_format_krw(item.line_total_krw))}</td>"
            "</tr>"
        )

    if is_pickup:
        shipping_html = (
            "<p style=\"margin:0 0 8px;font-size:14px;color:#1A1917;\"><strong>Самовывоз</strong></p>"
        )
        if pickup:
            shipping_html += (
                f"<p style=\"margin:0 0 8px;font-size:14px;color:#1A1917;line-height:1.5;\">"
                f"{_address_html(pickup)}</p>"
            )
        if br_number:
            shipping_html += (
                f"<p style=\"margin:0;font-size:14px;color:#1A1917;line-height:1.5;\">"
                f"Заберите заказ, предъявив номер <strong>{escape(br_number)}</strong>.</p>"
            )
    else:
        destination = escape(order.country or order.shipping_destination or "")
        address = escape(
            ", ".join(
                part
                for part in [
                    order.postal_code,
                    order.country,
                    order.city,
                    order.address,
                ]
                if part
            )
        )
        shipping_html = (
            f"<p style=\"margin:0 0 8px;font-size:14px;color:#1A1917;\">"
            f"<strong>Доставка EMS</strong>"
            f"{f' · {destination}' if destination else ''}</p>"
        )
        if order.shipping_krw:
            shipping_html += (
                f"<p style=\"margin:0 0 8px;font-size:14px;color:#8A8680;\">"
                f"Доставка: {escape(_format_krw(order.shipping_krw))}</p>"
            )
        if address:
            shipping_html += (
                f"<p style=\"margin:0;font-size:14px;color:#1A1917;line-height:1.5;\">"
                f"{address}</p>"
            )

    html = f"""<!DOCTYPE html>
<html lang="ru">
<body style="margin:0;padding:0;background:#F7F4EF;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F7F4EF;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#FFFFFF;border-radius:8px;padding:36px 32px;font-family:Inter,Lato,Arial,sans-serif;color:#1A1917;">
          <tr>
            <td>
              <p style="margin:0 0 4px;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#B89254;">Evacode</p>
              <h1 style="margin:0 0 20px;font-size:22px;font-weight:600;line-height:1.3;">Заказ оплачен</h1>
              <p style="margin:0 0 8px;font-size:15px;line-height:1.5;">Здравствуйте, {escape(order.first_name)}!</p>
              <p style="margin:0 0 24px;font-size:15px;line-height:1.5;color:#8A8680;">Спасибо за покупку. Ниже реквизиты заказа.</p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 28px;background:#F7F4EF;border-radius:6px;">
                <tr>
                  <td style="padding:16px 18px;">
                    <p style="margin:0 0 6px;font-size:12px;color:#8A8680;text-transform:uppercase;letter-spacing:0.06em;">Номер заказа</p>
                    <p style="margin:0 0 14px;font-size:20px;font-weight:600;color:#1A1917;">{escape(br_number or "—")}</p>
                    <p style="margin:0 0 6px;font-size:12px;color:#8A8680;text-transform:uppercase;letter-spacing:0.06em;">Сумма</p>
                    <p style="margin:0;font-size:16px;font-weight:600;">{escape(_format_krw(order.amount_krw))}
                      <span style="font-weight:400;color:#8A8680;"> · {escape(str(order.amount_usd))} USD</span>
                    </p>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 12px;font-size:13px;letter-spacing:0.06em;text-transform:uppercase;color:#8A8680;">Состав</p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 28px;font-size:14px;">
                <tr>
                  <th align="left" style="padding:0 0 8px;font-weight:500;color:#8A8680;border-bottom:1px solid #E8E4DE;">Товар</th>
                  <th align="center" style="padding:0 0 8px;font-weight:500;color:#8A8680;border-bottom:1px solid #E8E4DE;">Кол-во</th>
                  <th align="right" style="padding:0 0 8px;font-weight:500;color:#8A8680;border-bottom:1px solid #E8E4DE;">Сумма</th>
                </tr>
                {"".join(rows)}
              </table>
              <div style="margin:0 0 28px;padding-top:4px;border-top:1px solid #E8E4DE;">
                <p style="margin:20px 0 12px;font-size:13px;letter-spacing:0.06em;text-transform:uppercase;color:#8A8680;">Получение</p>
                {shipping_html}
              </div>
              <p style="margin:0;font-size:13px;color:#8A8680;line-height:1.5;">
                Вопросы: <a href="mailto:orders@evacode.co.kr" style="color:#B89254;text-decoration:none;">orders@evacode.co.kr</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return text, html


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

    subject = f"Evacode — заказ {br_number} оплачен"
    text, html = build_order_confirmation_bodies(order)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or settings.EMAIL_HOST_USER
    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=from_email,
        to=[order.email.strip()],
    )
    message.attach_alternative(html, "text/html")
    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Не удалось отправить письмо по заказу %s", order.public_id)
        return False

    order.confirmation_email_sent_at = timezone.now()
    order.save(update_fields=["confirmation_email_sent_at", "updated_at"])
    return True
