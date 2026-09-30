from .order_email import _format_krw
from .shipping import METHOD_PICKUP


def _clean(value) -> str:
    return str(value or "").strip()


def build_consult_text(user: dict) -> str:
    lines = ["ЗАЯВКА НА КОНСУЛЬТАЦИЮ С САЙТА"]
    name = _clean(user.get("name") or user.get("firstName"))
    if name:
        lines.append(f"Имя: {name}")
    lines.append(f"Телефон: {_clean(user.get('phone'))}")
    return "\n".join(lines)


def build_manager_order_text(order, items) -> str:
    lines = [
        "ЗАКАЗ С САЙТА — ОФОРМИТЬ С КЛИЕНТОМ (не оплачен)",
        f"№ {order.public_id}",
        "",
        "СОСТАВ",
    ]
    lines.extend(
        f"• {item.title} — {item.quantity} шт × {_format_krw(item.price_krw)} = {_format_krw(item.line_total_krw)}"
        for item in items
    )
    lines.append(f"Товары: {_format_krw(order.goods_krw)}")
    if order.shipping_method == METHOD_PICKUP:
        lines.append("Доставка: самовывоз")
    else:
        weight = f", {order.weight_grams} г" if order.weight_grams else ""
        lines.append(f"Доставка EMS: {_format_krw(order.shipping_krw)}{weight}")
    usd = f" (≈ {order.amount_usd} USD)" if order.amount_usd else ""
    lines.append(f"Итого: {_format_krw(order.amount_krw)}{usd}")

    lines.extend(["", "КЛИЕНТ"])
    lines.append(f"Имя: {order.first_name}")
    lines.append(f"Телефон: {order.phone}")
    lines.append(f"Email: {order.email}")
    if order.shipping_method == METHOD_PICKUP:
        lines.append("Получение: самовывоз")
    else:
        address = ", ".join(
            part for part in (order.postal_code, order.country, order.city, order.address) if part
        )
        lines.append(f"Адрес: {address}")
    if order.comment:
        lines.append(f"Комментарий: {order.comment}")
    return "\n".join(lines)
