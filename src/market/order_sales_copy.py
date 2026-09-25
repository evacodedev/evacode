"""Текст обращения клиента с сайта для передачи в отдел продаж."""

from .shipping import METHOD_PICKUP


def _shipping_line(order) -> str:
    if order.shipping_method == METHOD_PICKUP:
        return "Доставка: самовывоз"
    if order.shipping_method == "ems" or order.shipping_krw:
        destination = order.shipping_destination or order.country or ""
        weight = f", {order.weight_grams} г" if order.weight_grams else ""
        label = f"Доставка EMS {destination}".strip()
        if order.shipping_krw:
            return f"{label}: {order.shipping_krw} ₩{weight}"
        return f"{label}{weight}"
    return "Доставка: не указана"


def format_sales_inquiry(order) -> str:
    """Готовый текст для копирования в мессенджер / CRM отдела продаж."""
    lines = [
        "Обращение с сайта Evacode",
        f"№ {order.public_id}",
        f"Статус: {order.get_status_display()}",
        "",
        f"ФИО: {order.first_name}",
        f"Телефон: {order.phone}",
        f"Email: {order.email}",
        f"Адрес: {order.postal_code} {order.country}, {order.city}, {order.address}".strip(),
        _shipping_line(order),
        "",
        "Товары:",
    ]
    for item in order.items.all():
        lines.append(f"— {item.title} — {item.quantity} шт — {item.price_krw} ₩")
    lines.extend(
        [
            "",
            f"Товары: {order.goods_krw or 0} ₩",
            f"Доставка: {order.shipping_krw or 0} ₩",
            f"Итого: {order.amount_krw} ₩ / {order.amount_usd} USD",
        ]
    )
    if order.comment:
        lines.extend(["", f"Комментарий: {order.comment.strip()}"])
    return "\n".join(lines).strip() + "\n"
