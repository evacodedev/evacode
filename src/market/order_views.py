import json
import logging
import re

from asgiref.sync import async_to_sync
from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from urllib.parse import urljoin, urlencode

from .business_ru_orders import export_paid_order
from .currency import krw_to_usd
from .models import GoodsModel, SiteOrder, SiteOrderItem
from .paypal import PayPalError, capture_id_from_payload, capture_order, create_order, receipt_url

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _digits(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _public_base(url: str) -> str:
    base = (url or "").strip()
    if not base.startswith(("http://", "https://")):
        base = f"https://{base}"
    return base.rstrip("/") + "/"


def _frontend_url(path: str, query: dict | None = None) -> str:
    url = urljoin(_public_base(settings.FRONTEND_PUBLIC_URL), path.lstrip("/"))
    if query:
        url = f"{url}?{urlencode(query)}"
    return url


def _notify_telegram(order: SiteOrder):
    try:
        from .views import bot, chat_id, keyboard
    except Exception:
        return
    if not chat_id:
        return
    lines = [
        "ОПЛАЧЕННЫЙ ЗАКАЗ С САЙТА:",
        f"№ {order.public_id}",
        f"{order.amount_krw} ₩ / {order.amount_usd} USD",
        f"ФИО: {order.first_name}",
        f"Телефон: {order.phone}",
        f"Email: {order.email}",
        f"Адрес: {order.postal_code} {order.country}, {order.city}, {order.address}",
    ]
    for item in order.items.all():
        lines.append(f'{item.title} — {item.quantity} шт — {item.price_krw} ₩')
    if order.comment:
        lines.append(f"Комментарий: {order.comment}")
    if order.business_ru_order_id:
        lines.append(f"Business.Ru заказ: {order.business_ru_order_id}")
    elif order.business_ru_error:
        lines.append(f"Business.Ru: {order.business_ru_error}")
    try:
        async_to_sync(bot.send_message)(chat_id=chat_id, text="\n".join(lines), reply_markup=keyboard)
    except Exception:
        logger.exception("Не удалось отправить заказ %s в Telegram", order.public_id)


def _order_payload(order: SiteOrder) -> dict:
    items = []
    for item in order.items.select_related("good").all():
        image_url = ""
        if item.good:
            image = item.good.images.order_by("sort", "id").first()
            if image:
                image_url = image.url
        items.append(
            {
                "title": item.title,
                "quantity": item.quantity,
                "price_krw": item.price_krw,
                "image": image_url,
            }
        )
    return {
        "id": str(order.public_id),
        "status": order.status,
        "first_name": order.first_name,
        "phone": order.phone,
        "email": order.email,
        "country": order.country,
        "city": order.city,
        "address": order.address,
        "postal_code": order.postal_code,
        "amount_krw": order.amount_krw,
        "amount_usd": str(order.amount_usd),
        "paypal_capture_id": order.paypal_capture_id,
        "paypal_receipt_url": order.paypal_receipt_url,
        "items": items,
    }


def _complete_paid_order(order: SiteOrder, capture_data: dict) -> bool:
    paypal_status = capture_data.get("status")
    capture_id = capture_id_from_payload(capture_data)
    order.paypal_payload = json.dumps(capture_data, ensure_ascii=False)[:20000]
    if paypal_status != "COMPLETED":
        order.status = SiteOrder.Status.FAILED
        order.save(update_fields=["status", "paypal_payload", "updated_at"])
        return False

    if order.status != SiteOrder.Status.PAID:
        order.status = SiteOrder.Status.PAID
        order.paypal_capture_id = capture_id or order.paypal_capture_id
        order.paypal_receipt_url = receipt_url(order.paypal_capture_id)
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paypal_capture_id", "paypal_receipt_url", "paypal_payload", "paid_at", "updated_at"])
    elif not order.paypal_receipt_url and order.paypal_capture_id:
        order.paypal_receipt_url = receipt_url(order.paypal_capture_id)
        order.save(update_fields=["paypal_receipt_url", "paypal_payload", "updated_at"])

    if (
        not order.business_ru_order_id
        or not getattr(order, "business_ru_payment_id", "")
        or not getattr(order, "business_ru_reservation_id", "")
    ):
        try:
            export_paid_order(order)
        except Exception as exc:
            logger.exception("Выгрузка заказа %s в Business.Ru не удалась", order.public_id)
            order.business_ru_error = str(exc)[:4000]
            order.save(update_fields=["business_ru_error", "updated_at"])

    _notify_telegram(order)
    return True


class CreateSiteOrderView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.data if hasattr(request, "data") else {}
        user = data.get("user") or {}
        cart = data.get("cart") or []

        first_name = str(user.get("firstName") or "").strip()
        phone = str(user.get("phone") or "").strip()
        email = str(user.get("email") or "").strip().lower()
        country = str(user.get("country") or "").strip()
        city = str(user.get("city") or "").strip()
        address = str(user.get("address") or "").strip()
        postal_code = str(user.get("postalCode") or "").strip()
        comment = str(user.get("comment") or "").strip()

        errors = {}
        if len(first_name) < 2:
            errors["firstName"] = "Обязательное поле"
        if not phone:
            errors["phone"] = "Обязательное поле"
        if not email or not EMAIL_RE.match(email):
            errors["email"] = "Укажите корректный email"
        if not country:
            errors["country"] = "Обязательное поле"
        if not city:
            errors["city"] = "Обязательное поле"
        if not address:
            errors["address"] = "Обязательное поле"
        if not isinstance(cart, list) or not cart:
            errors["cart"] = "Корзина пуста"
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        prepared = []
        total_krw = 0
        for raw in cart:
            try:
                good_id = int(raw.get("id"))
                quantity = int(raw.get("quantity") or 0)
            except (TypeError, ValueError):
                return JsonResponse({"errors": {"cart": "Некорректная позиция"}}, status=400)
            if quantity < 1:
                return JsonResponse({"errors": {"cart": "Количество должно быть больше 0"}}, status=400)
            good = GoodsModel.objects.filter(id=good_id).first()
            if not good or not good.retail_price:
                return JsonResponse({"errors": {"cart": f"Товар {good_id} недоступен"}}, status=400)
            if good.stock is not None and quantity > good.stock:
                return JsonResponse({"errors": {"cart": f"Недостаточно остатка: {good.title}"}}, status=400)
            line_total = good.retail_price * quantity
            total_krw += line_total
            prepared.append((good, quantity, line_total))

        try:
            amount_usd, usd_snapshot = krw_to_usd(total_krw)
        except Exception as exc:
            logger.exception("Не удалось посчитать USD для заказа")
            return JsonResponse({"error": f"Не удалось посчитать сумму в USD: {exc}"}, status=503)
        if amount_usd < Decimal("0.01"):
            return JsonResponse({"error": "Сумма заказа слишком мала для PayPal"}, status=400)

        order = SiteOrder.objects.create(
            first_name=first_name[:128],
            phone=phone[:64],
            phone_digits=_digits(phone)[:32],
            email=email[:254],
            country=country[:64],
            city=city[:128],
            address=address[:255],
            postal_code=postal_code[:32],
            comment=comment[:2000],
            amount_krw=total_krw,
            amount_usd=amount_usd,
            usd_rate_snapshot=usd_snapshot,
        )
        SiteOrderItem.objects.bulk_create(
            [
                SiteOrderItem(
                    order=order,
                    good=good,
                    good_id_snapshot=good.id,
                    title=good.title,
                    quantity=quantity,
                    price_krw=good.retail_price,
                    line_total_krw=line_total,
                )
                for good, quantity, line_total in prepared
            ]
        )

        return_url = urljoin(
            _public_base(settings.BACKEND_PUBLIC_URL),
            reverse("site_order_paypal_return").lstrip("/"),
        )
        cancel_url = _frontend_url("/page/account/checkout", {"paypal": "cancel", "id": str(order.public_id)})
        try:
            paypal_order, approve_url = create_order(
                amount_usd=amount_usd,
                reference_id=order.public_id,
                return_url=return_url,
                cancel_url=cancel_url,
                description=f"Evacode {order.public_id}",
            )
        except PayPalError as exc:
            order.status = SiteOrder.Status.FAILED
            order.paypal_payload = str(exc.payload or exc)[:20000]
            order.save(update_fields=["status", "paypal_payload", "updated_at"])
            return JsonResponse({"error": str(exc)}, status=502)

        order.paypal_order_id = paypal_order.get("id") or ""
        order.paypal_payload = json.dumps(paypal_order, ensure_ascii=False)[:20000]
        order.save(update_fields=["paypal_order_id", "paypal_payload", "updated_at"])
        return JsonResponse(
            {
                "id": str(order.public_id),
                "approve_url": approve_url,
                "amount_usd": str(order.amount_usd),
                "amount_krw": order.amount_krw,
            }
        )


class SiteOrderDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, public_id):
        order = SiteOrder.objects.filter(public_id=public_id).first()
        if not order:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        return JsonResponse(_order_payload(order))


@method_decorator(csrf_exempt, name="dispatch")
class PayPalReturnView(View):
    def get(self, request):
        token = request.GET.get("token") or ""
        order = SiteOrder.objects.filter(paypal_order_id=token).first()
        if not order:
            return HttpResponseRedirect(_frontend_url("/page/account/checkout", {"paypal": "missing"}))
        if order.status == SiteOrder.Status.PAID:
            return HttpResponseRedirect(
                _frontend_url("/page/order-success", {"paypal": "1", "id": str(order.public_id)})
            )
        try:
            capture_data = capture_order(order.paypal_order_id)
        except PayPalError:
            logger.exception("Capture PayPal не удался для %s", order.public_id)
            order.status = SiteOrder.Status.FAILED
            order.save(update_fields=["status", "updated_at"])
            return HttpResponseRedirect(
                _frontend_url("/page/account/checkout", {"paypal": "fail", "id": str(order.public_id)})
            )
        paid = _complete_paid_order(order, capture_data)
        if not paid:
            return HttpResponseRedirect(
                _frontend_url("/page/account/checkout", {"paypal": "fail", "id": str(order.public_id)})
            )
        return HttpResponseRedirect(
            _frontend_url("/page/order-success", {"paypal": "1", "id": str(order.public_id)})
        )
