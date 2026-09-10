from .ems_tariffs import ems_price_krw
from .models import EmsDestination, GoodsModel

METHOD_EMS = "ems"
METHOD_PICKUP = "pickup"
METHODS = {METHOD_EMS, METHOD_PICKUP}


def chargeable_weight_grams(weight_grams: int) -> int:
    if weight_grams is None or weight_grams <= 0:
        return 0
    return ((int(weight_grams) + 99) // 100) * 100


def packing_weight_grams(goods_grams: int) -> int:
    if goods_grams is None or goods_grams <= 0:
        return 0
    if goods_grams <= 2000:
        return 500
    if goods_grams <= 5000:
        return 800
    if goods_grams <= 10000:
        return 1300
    return 2000


def parcel_weights(goods_grams: int) -> dict:
    goods = int(goods_grams or 0)
    packing = packing_weight_grams(goods)
    billed = chargeable_weight_grams(goods + packing) if goods else 0
    return {
        "weight_grams": goods,
        "packing_grams": packing,
        "chargeable_weight_grams": billed,
    }


def active_shipping_destinations():
    return [
        {
            "code": item.code,
            "name": item.name,
            "can_calculate": item.can_calculate,
        }
        for item in EmsDestination.objects.filter(is_active=True).order_by("sort", "code")
        if item.can_calculate
    ]


def parse_cart_lines(cart):
    if not isinstance(cart, list) or not cart:
        return None, "Корзина пуста"
    prepared = []
    goods_krw = 0
    for raw in cart:
        try:
            good_id = int(raw.get("id"))
            quantity = int(raw.get("quantity") or 0)
        except (TypeError, ValueError, AttributeError):
            return None, "Некорректная позиция"
        if quantity < 1:
            return None, "Количество должно быть больше 0"
        good = GoodsModel.objects.filter(id=good_id).first()
        if not good or not good.retail_price:
            return None, f"Товар {good_id} недоступен"
        if good.stock is not None and quantity > good.stock:
            return None, f"Недостаточно остатка: {good.title}"
        line_total = good.retail_price * quantity
        goods_krw += line_total
        prepared.append((good, quantity, line_total))
    return (prepared, goods_krw), None


def cart_weight_grams(prepared) -> tuple[int | None, str | None]:
    total = 0
    for good, quantity, _line in prepared:
        if good.weight is None or good.weight <= 0:
            return None, f"Нет веса у товара: {good.title}"
        total += good.weight * quantity
    return total, None


def quote_shipping(method, destination_code, prepared):
    method = (method or "").strip()
    destination_code = (destination_code or "").strip().upper()
    if method not in METHODS:
        return None, "Выберите способ доставки"

    if method == METHOD_PICKUP:
        weight, _weight_error = cart_weight_grams(prepared)
        weights = parcel_weights(weight or 0)
        return {
            "method": METHOD_PICKUP,
            "destination": "KR",
            "destination_name": "Самовывоз",
            **weights,
            "shipping_krw": 0,
        }, None

    if not destination_code:
        return None, "Выберите страну доставки"
    destination = EmsDestination.objects.filter(code=destination_code, is_active=True).first()
    if destination is None or not destination.can_calculate:
        return None, "Для этой страны нет тарифа EMS"

    weight, weight_error = cart_weight_grams(prepared)
    if weight_error:
        return None, weight_error
    weights = parcel_weights(weight)
    price = ems_price_krw(destination.code, weights["chargeable_weight_grams"])
    if price is None:
        return None, "Для этого веса нет тарифа EMS"
    return {
        "method": METHOD_EMS,
        "destination": destination.code,
        "destination_name": destination.name,
        **weights,
        "shipping_krw": price,
    }, None
