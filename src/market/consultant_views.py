import logging
import threading
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from .auth import OptionalJWTAuthentication
from .business_ru_clients import lookup_business_ru
from .business_ru_orders import export_consultant_order
from .consultant import (
    EMAIL_RE,
    LOOKUP_LIMIT_PER_HOUR,
    active_consultant,
    amount_to_krw,
    available_currencies,
    currency_codes,
    find_client,
    krw_to_display,
    normalize_lookup,
    order_paid_krw,
    payment_check,
)
from .currency import krw_to_usd
from .latin import LATIN_ONLY_MESSAGE, has_non_latin_letters
from .models import ConsultantClientLookup, SiteOrder, SiteOrderItem, SiteOrderPayment
from .order_email import send_order_confirmation_email
from .shipping import METHOD_EMS, METHOD_PICKUP, parse_cart_lines, quote_shipping

logger = logging.getLogger(__name__)

PROOF_MAX_BYTES = 5 * 1024 * 1024
PROOF_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "application/pdf"}
LATIN_FIELDS = ("first_name", "country", "city", "address", "postal_code")


class IsActiveConsultant(BasePermission):
    message = "Раздел доступен только консультантам"

    def has_permission(self, request, view):
        consultant = active_consultant(request.user)
        request.consultant = consultant
        return consultant is not None


class ConsultantAPIView(APIView):
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [IsActiveConsultant]

    def own_order(self, request, public_id):
        return (
            SiteOrder.objects.filter(public_id=public_id, consultant=request.consultant)
            .prefetch_related("items__good__images", "payments")
            .first()
        )


def _digits(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _image_url(good) -> str:
    if good is None:
        return ""
    image = good.images.order_by("sort", "id").first()
    return image.url if image else ""


def _validate_draft(data: dict):
    client = data.get("client") or {}
    shipping = data.get("shipping") or {}
    method = str(shipping.get("method") or METHOD_EMS).strip()
    destination = str(shipping.get("destination") or "").strip().upper()
    form = {
        "first_name": str(client.get("first_name") or "").strip(),
        "phone": str(client.get("phone") or "").strip(),
        "email": str(client.get("email") or "").strip().lower(),
        "country": str(client.get("country") or "").strip(),
        "city": str(client.get("city") or "").strip(),
        "address": str(client.get("address") or "").strip(),
        "postal_code": str(client.get("postal_code") or "").strip(),
        "comment": str(client.get("comment") or "").strip(),
        "business_ru_partner_id": _digits(client.get("business_ru_partner_id"))[:32],
    }
    errors = {}
    if len(form["first_name"]) < 2:
        errors["first_name"] = "Укажите имя клиента"
    if len(_digits(form["phone"])) < 7:
        errors["phone"] = "Укажите телефон клиента"
    if form["email"] and not EMAIL_RE.match(form["email"]):
        errors["email"] = "Укажите корректный email"
    latin_fields = LATIN_FIELDS if method == METHOD_EMS else ("first_name",)
    for field in latin_fields:
        if form[field] and has_non_latin_letters(form[field]):
            errors.setdefault(field, LATIN_ONLY_MESSAGE)
    if method == METHOD_PICKUP:
        destination = "KR"
        form["country"] = form["country"] or "Корея"
        form["city"] = form["city"] or "Самовывоз"
        form["address"] = form["address"] or "Самовывоз"
    elif method == METHOD_EMS:
        if not destination:
            errors["destination"] = "Укажите страну"
        for field, message in (
            ("country", "Укажите страну"),
            ("city", "Укажите город"),
            ("address", "Укажите адрес"),
            ("postal_code", "Укажите индекс"),
        ):
            if not form[field]:
                errors.setdefault(field, message)
    else:
        errors["shipping"] = "Выберите способ доставки"

    currency = str(data.get("display_currency") or "KRW").strip().upper()
    if currency not in currency_codes():
        errors["display_currency"] = "Валюта недоступна"

    parsed, cart_error = parse_cart_lines(data.get("cart") or [])
    if cart_error:
        errors["cart"] = cart_error
    quote = None
    if parsed and not errors.get("shipping") and not errors.get("destination"):
        quote, shipping_error = quote_shipping(method, destination, parsed[0])
        if shipping_error:
            errors["shipping"] = shipping_error
    if errors:
        return None, errors
    prepared, goods_krw = parsed
    return {"form": form, "prepared": prepared, "goods_krw": goods_krw, "quote": quote, "currency": currency}, {}


def _apply_draft(order: SiteOrder, draft: dict) -> SiteOrder:
    form, quote, goods_krw = draft["form"], draft["quote"], draft["goods_krw"]
    total_krw = goods_krw + quote["shipping_krw"]
    try:
        amount_usd, usd_snapshot = krw_to_usd(total_krw)
    except Exception:
        logger.warning("Курс USD недоступен для черновика консультанта", exc_info=True)
        amount_usd, usd_snapshot = Decimal("0"), None
    display_amount, display_rate = krw_to_display(total_krw, draft["currency"])

    order.first_name = form["first_name"][:128]
    order.phone = form["phone"][:64]
    order.phone_digits = _digits(form["phone"])[:32]
    order.email = form["email"][:254]
    order.country = form["country"][:64]
    order.city = form["city"][:128]
    order.address = form["address"][:255]
    order.postal_code = form["postal_code"][:32]
    order.comment = form["comment"][:2000]
    order.business_ru_partner_id = form["business_ru_partner_id"]
    order.shipping_method = quote["method"]
    order.shipping_destination = quote["destination"]
    order.shipping_krw = quote["shipping_krw"]
    order.goods_krw = goods_krw
    order.weight_grams = ((quote["weight_grams"] or 0) + (quote.get("packing_grams") or 0)) or None
    order.amount_krw = total_krw
    order.amount_usd = amount_usd
    order.usd_rate_snapshot = usd_snapshot
    order.display_currency = draft["currency"]
    order.display_rate = display_rate
    order.display_amount = display_amount
    order.save()

    order.items.all().delete()
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
            for good, quantity, line_total in draft["prepared"]
        ]
    )
    return order


def _payment_payload(order: SiteOrder, payment: SiteOrderPayment) -> dict:
    return {
        "id": payment.pk,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "rate": str(payment.rate),
        "amount_krw": payment.amount_krw,
        "has_proof": bool(payment.proof_name),
        "proof_name": payment.proof_name,
        "proof_is_image": (payment.proof_content_type or "").lower().startswith("image/"),
        "in_business_ru": bool(payment.business_ru_payment_id),
        "proof_url": f"/market/consultant/orders/{order.public_id}/payments/{payment.pk}/proof/",
        "business_ru_payment_number": payment.business_ru_payment_number,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }


def _export_complete(order: SiteOrder) -> bool:
    if not (order.business_ru_order_id and order.business_ru_reservation_id):
        return False
    return not order.payments.filter(business_ru_payment_id="").exists()


def _order_payload(order: SiteOrder, *, detail: bool = False) -> dict:
    data = {
        "id": str(order.public_id),
        "status": order.status,
        "status_label": order.get_status_display(),
        "is_draft": order.status == SiteOrder.Status.CONSULTANT_DRAFT,
        "sent_to_client_at": order.sent_to_client_at.isoformat() if order.sent_to_client_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "client_name": order.first_name,
        "amount_krw": order.amount_krw,
        "display_currency": order.display_currency or "KRW",
        "display_amount": str(order.display_amount) if order.display_amount is not None else None,
        "paid_krw": order_paid_krw(order),
        "item_count": sum(item.quantity for item in order.items.all()),
        "business_ru_order_number": order.business_ru_order_number,
        "business_ru_error": order.business_ru_error,
        "exporting": order.status == SiteOrder.Status.PAID and not order.business_ru_error and not _export_complete(order),
        "underpaid_krw": order.underpaid_krw,
    }
    if not detail:
        return data
    data.update(
        {
            "client": {
                "first_name": order.first_name,
                "phone": order.phone,
                "email": order.email,
                "country": order.country,
                "city": order.city if order.shipping_method != METHOD_PICKUP else "",
                "address": order.address if order.shipping_method != METHOD_PICKUP else "",
                "postal_code": order.postal_code,
                "comment": order.comment,
                "business_ru_partner_id": order.business_ru_partner_id,
            },
            "shipping": {
                "method": order.shipping_method,
                "destination": order.shipping_destination,
                "shipping_krw": order.shipping_krw,
                "weight_grams": order.weight_grams,
            },
            "goods_krw": order.goods_krw,
            "items": [
                {
                    "id": item.good_id_snapshot,
                    "title": item.title,
                    "quantity": item.quantity,
                    "price_krw": item.price_krw,
                    "line_total_krw": item.line_total_krw,
                    "image": _image_url(item.good),
                    "stock": item.good.stock if item.good else None,
                }
                for item in order.items.all()
            ],
            "payments": [_payment_payload(order, payment) for payment in order.payments.all()],
            "check": payment_check(order),
            "underpaid_reason": order.underpaid_reason,
            "business_ru_reservation_number": order.business_ru_reservation_number,
        }
    )
    return data


def _export_in_background(order_id: int) -> None:
    from django.db import close_old_connections

    close_old_connections()
    try:
        order = SiteOrder.objects.filter(pk=order_id).select_related("consultant__user").first()
        if order is None:
            return
        try:
            export_consultant_order(order)
        except Exception as exc:
            logger.exception("Выгрузка заказа консультанта %s в Business.Ru не удалась", order.public_id)
            order.refresh_from_db()
            if not order.business_ru_error:
                order.business_ru_error = str(exc)[:4000]
                order.save(update_fields=["business_ru_error", "updated_at"])
            return
        order.refresh_from_db()
        try:
            send_order_confirmation_email(order)
        except Exception:
            logger.exception("Письмо по заказу консультанта %s не отправлено", order.public_id)
    finally:
        close_old_connections()


def _start_export(order_id: int) -> None:
    threading.Thread(target=_export_in_background, args=(order_id,), daemon=True).start()


class ConsultantMeView(ConsultantAPIView):
    def get(self, request):
        user = request.consultant.user
        return JsonResponse(
            {
                "name": user.get_full_name() or user.email,
                "email": user.email,
                "currencies": available_currencies(),
            }
        )


class ConsultantOrdersView(ConsultantAPIView):
    def get(self, request):
        orders = (
            SiteOrder.objects.filter(consultant=request.consultant)
            .prefetch_related("items", "payments")
            .order_by("-created_at")
        )
        return JsonResponse({"results": [_order_payload(order) for order in orders]})

    def post(self, request):
        draft, errors = _validate_draft(request.data)
        if errors:
            return JsonResponse({"errors": errors}, status=400)
        with transaction.atomic():
            order = SiteOrder(
                status=SiteOrder.Status.CONSULTANT_DRAFT,
                consultant=request.consultant,
                amount_krw=0,
                amount_usd=Decimal("0"),
            )
            _apply_draft(order, draft)
        return JsonResponse(_order_payload(self.own_order(request, order.public_id), detail=True), status=201)


class ConsultantOrderDetailView(ConsultantAPIView):
    def get(self, request, public_id):
        order = self.own_order(request, public_id)
        if order is None:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        return JsonResponse(_order_payload(order, detail=True))

    def put(self, request, public_id):
        order = self.own_order(request, public_id)
        if order is None:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        if order.status != SiteOrder.Status.CONSULTANT_DRAFT:
            return JsonResponse({"error": "Заказ уже оформлен, менять его нельзя"}, status=409)
        draft, errors = _validate_draft(request.data)
        if errors:
            return JsonResponse({"errors": errors}, status=400)
        with transaction.atomic():
            _apply_draft(order, draft)
        return JsonResponse(_order_payload(self.own_order(request, public_id), detail=True))

    def delete(self, request, public_id):
        order = self.own_order(request, public_id)
        if order is None:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        if order.status != SiteOrder.Status.CONSULTANT_DRAFT:
            return JsonResponse({"error": "Оформленный заказ удалить нельзя"}, status=409)
        order.delete()
        return JsonResponse({"ok": True})


class ConsultantOrderSentView(ConsultantAPIView):
    """«Отправил клиенту на оплату» (`sent: true`) или «Вернуть в черновики» (`sent: false`)."""

    def post(self, request, public_id):
        order = self.own_order(request, public_id)
        if order is None:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        if order.status != SiteOrder.Status.CONSULTANT_DRAFT:
            return JsonResponse({"error": "Заказ уже оформлен"}, status=409)
        sent = request.data.get("sent")
        if sent is True or str(sent).lower() == "true":
            order.sent_to_client_at = order.sent_to_client_at or timezone.now()
        else:
            if order.payments.exists():
                return JsonResponse({"error": "По заказу уже есть оплата — вернуть в черновики нельзя"}, status=409)
            order.sent_to_client_at = None
        order.save(update_fields=["sent_to_client_at", "updated_at"])
        return JsonResponse(_order_payload(self.own_order(request, public_id), detail=True))


def _parse_payment(request, *, proof_required: bool) -> tuple[dict, dict]:
    """Сумма, валюта и фото оплаты; ₩ — по коммерческому курсу на момент запроса."""
    errors = {}
    currency = str(request.data.get("currency") or "").strip().upper()
    if currency not in currency_codes():
        errors["currency"] = "Выберите валюту"
    try:
        amount = Decimal(str(request.data.get("amount") or "").replace(",", ".").replace(" ", ""))
    except InvalidOperation:
        amount = Decimal("0")
    if amount <= 0:
        errors["amount"] = "Укажите сумму оплаты"
    proof = request.FILES.get("proof")
    if proof is None:
        if proof_required:
            errors["proof"] = "Приложите фото подтверждения оплаты"
    elif proof.size > PROOF_MAX_BYTES:
        errors["proof"] = "Файл больше 5 МБ"
    elif (proof.content_type or "").lower() not in PROOF_CONTENT_TYPES:
        errors["proof"] = "Нужна картинка (JPG, PNG, WEBP) или PDF"
    if errors:
        return {}, errors
    try:
        amount_krw, rate = amount_to_krw(amount, currency)
    except ValueError as exc:
        return {}, {"currency": str(exc)}
    fields = {
        "amount": amount.quantize(Decimal("0.01")),
        "currency": currency,
        "rate": rate,
        "amount_krw": amount_krw,
    }
    if proof is not None:
        fields.update(
            {
                "proof_name": (proof.name or "payment")[:255],
                "proof_content_type": (proof.content_type or "")[:100],
                "proof_data": proof.read(),
            }
        )
    return fields, {}


class ConsultantPaymentsView(ConsultantAPIView):
    def post(self, request, public_id):
        order = self.own_order(request, public_id)
        if order is None:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        if order.status != SiteOrder.Status.CONSULTANT_DRAFT:
            return JsonResponse({"error": "Заказ уже оформлен"}, status=409)
        fields, errors = _parse_payment(request, proof_required=True)
        if errors:
            return JsonResponse({"errors": errors}, status=400)
        with transaction.atomic():
            SiteOrderPayment.objects.create(order=order, created_by=request.user, **fields)
            if order.sent_to_client_at is None:
                order.sent_to_client_at = timezone.now()
                order.save(update_fields=["sent_to_client_at", "updated_at"])
        return JsonResponse(_order_payload(self.own_order(request, public_id), detail=True), status=201)


class ConsultantPaymentDetailView(ConsultantAPIView):
    def put(self, request, public_id, payment_id):
        order = self.own_order(request, public_id)
        if order is None:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        if order.status != SiteOrder.Status.CONSULTANT_DRAFT:
            return JsonResponse({"error": "Заказ уже оформлен, оплату менять нельзя"}, status=409)
        payment = order.payments.filter(pk=payment_id).first()
        if payment is None:
            return JsonResponse({"error": "Оплата не найдена"}, status=404)
        if payment.business_ru_payment_id:
            return JsonResponse({"error": "Оплата уже в системе заказов EvaCode, менять её нельзя"}, status=409)
        fields, errors = _parse_payment(request, proof_required=False)
        if errors:
            return JsonResponse({"errors": errors}, status=400)
        for name, value in fields.items():
            setattr(payment, name, value)
        payment.save(update_fields=list(fields))
        return JsonResponse(_order_payload(self.own_order(request, public_id), detail=True))

    def delete(self, request, public_id, payment_id):
        order = self.own_order(request, public_id)
        if order is None:
            return JsonResponse({"error": "Заказ не найден"}, status=404)
        if order.status != SiteOrder.Status.CONSULTANT_DRAFT:
            return JsonResponse({"error": "Заказ уже оформлен"}, status=409)
        deleted, _ = order.payments.filter(pk=payment_id).delete()
        if not deleted:
            return JsonResponse({"error": "Оплата не найдена"}, status=404)
        return JsonResponse(_order_payload(self.own_order(request, public_id), detail=True))


class ConsultantPaymentProofView(APIView):
    """Фото оплаты: только консультант-владелец заказа или staff (в том числе из админки по сессии)."""

    authentication_classes = [OptionalJWTAuthentication, SessionAuthentication]
    permission_classes = []

    def get(self, request, public_id, payment_id):
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return JsonResponse({"error": "Нужен вход"}, status=401)
        payment = (
            SiteOrderPayment.objects.select_related("order__consultant")
            .filter(pk=payment_id, order__public_id=public_id)
            .first()
        )
        if payment is None or not payment.proof_name:
            return JsonResponse({"error": "Файл не найден"}, status=404)
        if not user.is_staff:
            consultant = active_consultant(user)
            if consultant is None or payment.order.consultant_id != consultant.pk:
                return JsonResponse({"error": "Файл не найден"}, status=404)
        response = HttpResponse(bytes(payment.proof_data), content_type=payment.proof_content_type or "application/octet-stream")
        response["Content-Disposition"] = f'inline; filename="payment-{payment.pk}"'
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class ConsultantSubmitView(ConsultantAPIView):
    """«Оплата подтверждена, оформить»: только теперь заказ уходит в Business.Ru."""

    def post(self, request, public_id):
        with transaction.atomic():
            order = (
                SiteOrder.objects.select_for_update()
                .filter(public_id=public_id, consultant=request.consultant)
                .first()
            )
            if order is None:
                return JsonResponse({"error": "Заказ не найден"}, status=404)
            if order.status == SiteOrder.Status.PAID:
                if order.business_ru_error and not _export_complete(order):
                    order.business_ru_error = ""
                    order.save(update_fields=["business_ru_error", "updated_at"])
                    transaction.on_commit(lambda: _start_export(order.pk))
                    return JsonResponse(_order_payload(order, detail=True), status=202)
                return JsonResponse({"error": "Заказ уже оформлен"}, status=409)
            if order.status != SiteOrder.Status.CONSULTANT_DRAFT:
                return JsonResponse({"error": "Этот заказ нельзя оформить"}, status=409)
            if not order.payments.exists():
                return JsonResponse({"error": "Добавьте оплату с фото подтверждения"}, status=400)
            check = payment_check(order)
            if check["shortfall_krw"]:
                return JsonResponse(
                    {
                        "error": "Оплачено не полностью — оформить можно только после доплаты",
                        "code": "underpaid",
                        "check": check,
                    },
                    status=409,
                )
            order.status = SiteOrder.Status.PAID
            order.paid_at = timezone.now()
            order.underpaid_krw = 0
            order.underpaid_reason = ""
            order.business_ru_error = ""
            order.save(
                update_fields=["status", "paid_at", "underpaid_krw", "underpaid_reason", "business_ru_error", "updated_at"]
            )
            transaction.on_commit(lambda: _start_export(order.pk))
        return JsonResponse(_order_payload(self.own_order(request, public_id), detail=True), status=202)


class ConsultantClientLookupView(ConsultantAPIView):
    def get(self, request):
        consultant = request.consultant
        recent = ConsultantClientLookup.objects.filter(
            consultant=consultant, created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        if recent >= LOOKUP_LIMIT_PER_HOUR:
            return JsonResponse({"error": "Слишком много поисков за час. Попробуйте позже."}, status=429)
        query = str(request.GET.get("q") or "").strip()[:254]
        normalized = normalize_lookup(query)
        if normalized is None:
            return JsonResponse(
                {"error": "Введите полный телефон (с кодом страны) или email клиента"}, status=400
            )
        kind, value = normalized
        client = find_client(kind, value)
        business_ru = lookup_business_ru(query if kind == "email" else "", value if kind == "phone" else "")
        found = client is not None or bool(business_ru["matches"])
        ConsultantClientLookup.objects.create(consultant=consultant, query=query, found=found)
        if not found:
            message = "Клиент не найден ни на сайте, ни в системе заказов EvaCode. Заполните данные вручную."
            if business_ru["error"]:
                message = f"Клиент не найден на сайте. {business_ru['error']}. Заполните данные вручную."
            return JsonResponse({"error": message, "business_ru": business_ru}, status=404)
        return JsonResponse({"client": client, "business_ru": business_ru})
