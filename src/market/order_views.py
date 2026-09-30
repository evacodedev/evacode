import json
import logging
import re
import threading

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from urllib.parse import urljoin, urlencode

from django.db.models import Q

from .auth import OptionalJWTAuthentication

from .business_ru_orders import export_paid_order
from .checkout_request import build_manager_order_text
from .manager_notify import notify_managers
from .order_email import send_order_confirmation_email, send_order_help_email
from .currency import krw_to_usd
from .models import CheckoutSettings, SiteOrder, SiteOrderItem
from .paypal import (
    PayPalError,
    capture_id_from_payload,
    capture_order,
    create_order,
    receipt_url,
    resolve_paypal_mode,
    user_uses_paypal_sandbox,
)
from .shipping import (
    METHOD_EMS,
    METHOD_PICKUP,
    active_shipping_destinations,
    cart_weight_grams,
    parcel_weights,
    parse_cart_lines,
    quote_shipping,
)

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MANAGER_ORDER_REPEAT_WINDOW = timedelta(minutes=5)


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
    title = (
        "ТЕСТ PAYPAL SANDBOX:"
        if (order.paypal_mode or "").lower() == "sandbox"
        else "ОПЛАЧЕННЫЙ ЗАКАЗ С САЙТА:"
    )
    lines = [
        title,
        f"№ {order.public_id}",
        f"{order.amount_krw} ₩ / {order.amount_usd} USD",
        f"ФИО: {order.first_name}",
        f"Телефон: {order.phone}",
        f"Email: {order.email}",
        f"Адрес: {order.postal_code} {order.country}, {order.city}, {order.address}",
        _shipping_telegram_line(order),
    ]
    for item in order.items.all():
        lines.append(f'{item.title} — {item.quantity} шт — {item.price_krw} ₩')
    if order.comment:
        lines.append(f"Комментарий: {order.comment}")
    if order.business_ru_order_id:
        lines.append(f"Business.Ru заказ: {order.business_ru_order_id}")
    elif order.business_ru_error:
        lines.append(f"Business.Ru: {order.business_ru_error}")
    if not notify_managers("\n".join(lines), subject=f"{title.rstrip(':')} {order.public_id}", reply_to=order.email):
        logger.error("Заказ %s не дошёл ни в Telegram, ни на почту", order.public_id)


def _shipping_telegram_line(order: SiteOrder) -> str:
    if order.shipping_method == METHOD_PICKUP:
        return "Доставка: самовывоз"
    if order.shipping_krw:
        destination = order.country or order.shipping_destination
        weight = f", {order.weight_grams} г" if order.weight_grams else ""
        return f"Доставка EMS {destination}: {order.shipping_krw} ₩{weight}"
    return "Доставка: не указана"


def _order_list_item(order: SiteOrder) -> dict:
    items = []
    for item in order.items.all():
        image_url = ""
        good = getattr(item, "good", None)
        if good is not None:
            image = good.images.order_by("sort", "id").first()
            if image:
                image_url = image.url
        items.append(
            {
                "title": item.title,
                "quantity": item.quantity,
                "price_krw": item.price_krw,
                "line_total_krw": item.line_total_krw,
                "image": image_url,
            }
        )
    return {
        "id": str(order.public_id),
        "status": order.status,
        "status_label": order.get_status_display(),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "amount_krw": order.amount_krw,
        "amount_usd": str(order.amount_usd),
        "shipping_method": order.shipping_method,
        "business_ru_order_number": order.business_ru_order_number or "",
        "paypal_mode": order.paypal_mode or "",
        "item_count": sum(item["quantity"] for item in items),
        "items": items,
    }


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
        "shipping_method": order.shipping_method,
        "shipping_destination": order.shipping_destination,
        "shipping_krw": order.shipping_krw,
        "goods_krw": order.goods_krw,
        "weight_grams": order.weight_grams,
        "amount_krw": order.amount_krw,
        "amount_usd": str(order.amount_usd),
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
        order.paypal_receipt_url = receipt_url(order.paypal_capture_id, mode=order.paypal_mode)
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paypal_capture_id", "paypal_receipt_url", "paypal_payload", "paid_at", "updated_at"])
    elif not order.paypal_receipt_url and order.paypal_capture_id:
        order.paypal_receipt_url = receipt_url(order.paypal_capture_id, mode=order.paypal_mode)
        order.save(update_fields=["paypal_receipt_url", "paypal_payload", "updated_at"])

    # PayPal is already PAID here. BR/Telegram run in the background so the
    # return URL is not blocked. If documents are missing, retry from admin:
    # «Выгрузить в Business.Ru» or `export_site_order`.
    threading.Thread(
        target=_export_paid_side_effects,
        args=(order.pk,),
        daemon=True,
    ).start()
    return True


def _export_paid_side_effects(order_id: int) -> None:
    from django.db import close_old_connections

    close_old_connections()
    try:
        order = SiteOrder.objects.filter(pk=order_id).first()
        if not order:
            return
        if (
            not order.business_ru_order_id
            or not getattr(order, "business_ru_payment_id", "")
            or not getattr(order, "business_ru_reservation_id", "")
        ):
            try:
                export_paid_order(order)
                order.refresh_from_db()
            except Exception as exc:
                logger.exception("Выгрузка заказа %s в Business.Ru не удалась", order.public_id)
                order.business_ru_error = str(exc)[:4000]
                order.save(update_fields=["business_ru_error", "updated_at"])
        if order.business_ru_order_id or order.business_ru_order_number:
            try:
                send_order_confirmation_email(order)
            except Exception:
                logger.exception("Письмо по заказу %s не отправлено", order.public_id)
        _notify_telegram(order)
    finally:
        close_old_connections()


def _validate_order_request(data: dict):
    """Возвращает (form, prepared, goods_krw, quote, errors) для формы оформления."""
    user = data.get("user") or {}
    cart = data.get("cart") or []
    shipping = data.get("shipping") or {}
    shipping_method = str(shipping.get("method") or "").strip()
    shipping_destination = str(shipping.get("destination") or "").strip()

    form = {
        "first_name": str(user.get("firstName") or "").strip(),
        "phone": str(user.get("phone") or "").strip(),
        "email": str(user.get("email") or "").strip().lower(),
        "country": str(user.get("country") or "").strip(),
        "city": str(user.get("city") or "").strip(),
        "address": str(user.get("address") or "").strip(),
        "postal_code": str(user.get("postalCode") or "").strip(),
        "comment": str(user.get("comment") or "").strip(),
    }
    if shipping_method == METHOD_PICKUP:
        form["country"] = form["country"] or "Корея"
        form["city"] = form["city"] or "Самовывоз"
        form["address"] = form["address"] or "Самовывоз"

    errors = {}
    if len(form["first_name"]) < 2:
        errors["firstName"] = "Обязательное поле"
    if not form["phone"]:
        errors["phone"] = "Обязательное поле"
    if not form["email"] or not EMAIL_RE.match(form["email"]):
        errors["email"] = "Укажите корректный email"
    if not form["country"]:
        errors["country"] = "Обязательное поле"
    if not form["city"]:
        errors["city"] = "Обязательное поле"
    if not form["address"]:
        errors["address"] = "Обязательное поле"
    if shipping_method != METHOD_PICKUP and not form["postal_code"]:
        errors["postalCode"] = "Обязательное поле"
    parsed, cart_error = parse_cart_lines(cart)
    if cart_error:
        errors["cart"] = cart_error
    quote = None
    if parsed:
        quote, shipping_error = quote_shipping(shipping_method, shipping_destination, parsed[0])
        if shipping_error:
            errors["shipping"] = shipping_error
    if errors:
        return form, None, 0, None, errors
    prepared, goods_krw = parsed
    return form, prepared, goods_krw, quote, {}


def _create_order_record(request, form, prepared, goods_krw, quote, **extra) -> SiteOrder:
    account_user = request.user if getattr(request.user, "is_authenticated", False) else None
    order = SiteOrder.objects.create(
        user=account_user,
        first_name=form["first_name"][:128],
        phone=form["phone"][:64],
        phone_digits=_digits(form["phone"])[:32],
        email=form["email"][:254],
        country=form["country"][:64],
        city=form["city"][:128],
        address=form["address"][:255],
        postal_code=form["postal_code"][:32],
        comment=form["comment"][:2000],
        shipping_method=quote["method"],
        shipping_destination=quote["destination"],
        shipping_krw=quote["shipping_krw"],
        goods_krw=goods_krw,
        weight_grams=((quote["weight_grams"] or 0) + (quote.get("packing_grams") or 0)) or None,
        amount_krw=goods_krw + quote["shipping_krw"],
        **extra,
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
    return order


class CreateSiteOrderView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWTAuthentication]

    def post(self, request):
        if not CheckoutSettings.load().paypal_enabled:
            return JsonResponse({"error": "Оплата PayPal сейчас выключена"}, status=403)

        data = request.data if hasattr(request, "data") else {}
        form, prepared, goods_krw, quote, errors = _validate_order_request(data)
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        total_krw = goods_krw + quote["shipping_krw"]
        try:
            amount_usd, usd_snapshot = krw_to_usd(total_krw)
        except Exception as exc:
            logger.exception("Не удалось посчитать USD для заказа")
            return JsonResponse({"error": f"Не удалось посчитать сумму в USD: {exc}"}, status=503)
        if amount_usd < Decimal("0.01"):
            return JsonResponse({"error": "Сумма заказа слишком мала для PayPal"}, status=400)

        paypal_mode = resolve_paypal_mode(request.user)
        order = _create_order_record(
            request,
            form,
            prepared,
            goods_krw,
            quote,
            amount_usd=amount_usd,
            usd_rate_snapshot=usd_snapshot,
            paypal_mode=paypal_mode,
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
                mode=paypal_mode,
            )
        except PayPalError as exc:
            order.status = SiteOrder.Status.FAILED
            order.paypal_payload = str(exc.payload or exc)[:20000]
            order.save(update_fields=["status", "paypal_payload", "updated_at"])
            return JsonResponse({"error": str(exc)}, status=502)

        order.paypal_order_id = paypal_order.get("id") or ""
        order.paypal_payload = json.dumps(paypal_order, ensure_ascii=False)[:20000]
        order.save(update_fields=["paypal_order_id", "paypal_payload", "paypal_mode", "updated_at"])
        return JsonResponse(
            {
                "id": str(order.public_id),
                "approve_url": approve_url,
                "amount_usd": str(order.amount_usd),
                "amount_krw": order.amount_krw,
                "shipping_krw": order.shipping_krw,
                "goods_krw": order.goods_krw,
            }
        )


def _notify_manager_order(order_id: int) -> None:
    from django.db import close_old_connections

    close_old_connections()
    try:
        order = SiteOrder.objects.filter(pk=order_id).first()
        if not order:
            return
        text = build_manager_order_text(order, order.items.all())
        if not notify_managers(text, subject=f"Заказ с сайта через консультанта {order.public_id}", reply_to=order.email):
            logger.error("Заказ %s не дошёл ни в Telegram, ни на почту", order.public_id)
    finally:
        close_old_connections()


class CreateTelegramOrderView(APIView):
    """Заказ без оплаты на сайте: сохраняется, уходит в группу консультантов, в Business.Ru не выгружается."""

    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWTAuthentication]

    def post(self, request):
        if not CheckoutSettings.load().telegram_enabled:
            return JsonResponse({"error": "Заказ через Telegram сейчас выключен"}, status=403)

        data = request.data if hasattr(request, "data") else {}
        form, prepared, goods_krw, quote, errors = _validate_order_request(data)
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        phone_digits = _digits(form["phone"])
        if phone_digits and SiteOrder.objects.filter(
            status=SiteOrder.Status.MANAGER,
            phone_digits=phone_digits[:32],
            created_at__gte=timezone.now() - MANAGER_ORDER_REPEAT_WINDOW,
        ).exists():
            return JsonResponse(
                {"error": "Заказ с этого телефона уже отправлен. Если нужно что-то изменить — напишите нам в WhatsApp или Telegram, контакты ниже."},
                status=429,
            )

        total_krw = goods_krw + quote["shipping_krw"]
        try:
            amount_usd, usd_snapshot = krw_to_usd(total_krw)
        except Exception:
            logger.warning("Курс USD недоступен, заказ через консультанта сохранён без суммы в USD", exc_info=True)
            amount_usd, usd_snapshot = Decimal("0"), None

        order = _create_order_record(
            request,
            form,
            prepared,
            goods_krw,
            quote,
            status=SiteOrder.Status.MANAGER,
            amount_usd=amount_usd,
            usd_rate_snapshot=usd_snapshot,
        )
        threading.Thread(target=_notify_manager_order, args=(order.pk,), daemon=True).start()
        return JsonResponse({"id": str(order.public_id)}, status=201)


class ShippingDestinationsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return JsonResponse({"results": active_shipping_destinations()})


class ShippingQuoteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.data if hasattr(request, "data") else {}
        parsed, cart_error = parse_cart_lines(data.get("cart") or [])
        if cart_error:
            return JsonResponse({"error": cart_error}, status=400)
        shipping = data.get("shipping") or data
        method = str(shipping.get("method") or "").strip()
        destination = str(shipping.get("destination") or "").strip()
        weight, _weight_error = cart_weight_grams(parsed[0])
        weight_payload = parcel_weights(weight or 0)
        if not method or (method == METHOD_EMS and not destination):
            return JsonResponse({**weight_payload, "shipping_krw": None})
        quote, shipping_error = quote_shipping(method, destination, parsed[0])
        if shipping_error:
            return JsonResponse({"error": shipping_error, **weight_payload}, status=400)
        return JsonResponse(quote)


class SiteOrderDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, public_id):
        order = SiteOrder.objects.filter(public_id=public_id).first()
        if not order:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        return JsonResponse(_order_payload(order))


class MySiteOrdersView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [OptionalJWTAuthentication]

    def get(self, request):
        email = (request.user.email or request.user.username or "").strip()
        if email:
            SiteOrder.objects.filter(user__isnull=True, email__iexact=email).update(user=request.user)
        queryset = (
            SiteOrder.objects.filter(Q(user=request.user) | Q(email__iexact=email))
            .prefetch_related("items", "items__good__images")
            .order_by("-created_at")
        )
        return JsonResponse({"results": [_order_list_item(order) for order in queryset]})


class SiteOrderHelpView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [OptionalJWTAuthentication]

    def post(self, request, public_id):
        email = (request.user.email or request.user.username or "").strip()
        order = (
            SiteOrder.objects.filter(public_id=public_id)
            .filter(Q(user=request.user) | Q(email__iexact=email))
            .first()
        )
        if not order:
            return JsonResponse({"error": "Заказ не найден"}, status=404)

        data = request.data if hasattr(request, "data") else {}
        phone = str(data.get("phone") or "").strip()
        message = str(data.get("message") or "").strip()
        errors = {}
        if not phone:
            errors["phone"] = "Укажите телефон"
        if len(message) < 3:
            errors["message"] = "Напишите вопрос"
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        try:
            send_order_help_email(order, request.user, phone, message)
        except Exception:
            logger.exception("Не удалось отправить помощь по заказу %s", order.public_id)
            return JsonResponse(
                {"error": "Не удалось отправить обращение. Напишите нам на orders@evacode.co.kr"},
                status=502,
            )
        return JsonResponse({"ok": True})


class CheckoutSettingsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWTAuthentication]

    def get(self, request):
        settings_row = CheckoutSettings.load()
        paypal_sandbox = bool(
            settings_row.paypal_enabled
            and resolve_paypal_mode(request.user) == "sandbox"
            and user_uses_paypal_sandbox(request.user)
        )
        return JsonResponse(
            {
                "paypal_enabled": settings_row.paypal_enabled,
                "telegram_enabled": settings_row.telegram_enabled,
                "paypal_sandbox": paypal_sandbox,
            }
        )


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
            capture_data = capture_order(
                order.paypal_order_id,
                mode=resolve_paypal_mode(stored_mode=order.paypal_mode),
            )
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
