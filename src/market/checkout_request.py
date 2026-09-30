from .order_email import _format_krw
from .shipping import METHOD_PICKUP, parse_cart_lines, quote_shipping


def _clean(value) -> str:
    return str(value or "").strip()


def build_consult_text(user: dict) -> str:
    lines = ["ЗАЯВКА НА КОНСУЛЬТАЦИЮ С САЙТА"]
    name = _clean(user.get("name") or user.get("firstName"))
    if name:
        lines.append(f"Имя: {name}")
    lines.append(f"Телефон: {_clean(user.get('phone'))}")
    return "\n".join(lines)


def _cart_lines(cart: list) -> tuple[list[str], int | None, list | None]:
    requested = [
        {"id": item.get("id"), "quantity": item.get("quantity")}
        for item in cart
        if isinstance(item, dict)
    ]
    parsed, error = parse_cart_lines(requested)
    if error:
        lines = [
            f"• {_clean(item.get('title'))} — {_clean(item.get('quantity'))} шт"
            for item in cart
            if isinstance(item, dict)
        ]
        lines.append(f"Проверка каталога: {error}")
        return lines, None, None
    prepared, goods_krw = parsed
    lines = [
        f"• {good.title} — {quantity} шт × {_format_krw(good.retail_price)} = {_format_krw(line_total)}"
        for good, quantity, line_total in prepared
    ]
    return lines, goods_krw, prepared


def build_telegram_order_text(data: dict) -> str:
    user = data.get("user") or {}
    cart = data.get("cart") or []
    shipping = data.get("shipping") or {}
    method = _clean(shipping.get("method"))

    item_lines, goods_krw, prepared = _cart_lines(cart if isinstance(cart, list) else [])
    lines = ["ЗАКАЗ С САЙТА (Telegram, без оплаты)", "", "СОСТАВ", *item_lines]

    quote = None
    quote_error = ""
    if prepared is not None:
        quote, quote_error = quote_shipping(method, shipping.get("destination"), prepared)
    if goods_krw is not None:
        lines.append(f"Товары: {_format_krw(goods_krw)}")
    if quote:
        lines.append(f"Доставка: {_format_krw(quote['shipping_krw'])}")
        if quote.get("chargeable_weight_grams"):
            lines.append(f"Вес к оплате: {quote['chargeable_weight_grams']} г")
        lines.append(f"Итого: {_format_krw(goods_krw + quote['shipping_krw'])}")
    elif quote_error:
        lines.append(f"Доставка: не посчитана ({quote_error})")

    lines.extend(["", "КЛИЕНТ"])
    lines.append(f"Имя: {_clean(user.get('firstName'))}")
    lines.append(f"Телефон: {_clean(user.get('phone'))}")
    email = _clean(user.get("email"))
    if email:
        lines.append(f"Email: {email}")

    if method == METHOD_PICKUP:
        lines.append("Получение: самовывоз")
    else:
        lines.append(f"Получение: EMS {_clean(user.get('country'))}".rstrip())
        address = ", ".join(
            part
            for part in (
                _clean(user.get("postalCode")),
                _clean(user.get("country")),
                _clean(user.get("city")),
                _clean(user.get("address")),
            )
            if part
        )
        if address:
            lines.append(f"Адрес: {address}")
    comment = _clean(user.get("comment"))
    if comment:
        lines.append(f"Комментарий: {comment}")
    return "\n".join(lines)
