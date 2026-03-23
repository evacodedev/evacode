import json
import time
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.http import HttpResponseNotAllowed
from django.shortcuts import render
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from finance.models import InvoiceTossPayments


CONFIRM_RETRYABLE_ERROR_CODES = {
    "FAILED_PAYMENT_INTERNAL_SYSTEM_PROCESSING",
    "NOT_FOUND_PAYMENT_TO_CONFIRM",
}
CONFIRM_RETRY_ATTEMPTS = 3
CONFIRM_RETRY_DELAY_SECONDS = 1


def _default_home_url():
    return getattr(settings, "EVACODE_FRONTEND_URL", "https://www.evacode.org")


def _parse_error(response):
    try:
        data = response.json()
    except ValueError:
        return f"HTTP_{response.status_code}", response.text or "Unknown error"

    return data.get("code", f"HTTP_{response.status_code}"), data.get("message", response.text or "Unknown error")


def _normalize_amount(raw_amount, invoice):
    amount_value = raw_amount if raw_amount not in (None, "") else (invoice.amount if invoice else None)
    if amount_value is None:
        return None

    try:
        decimal_amount = Decimal(str(amount_value))
    except InvalidOperation:
        return None

    if decimal_amount == decimal_amount.to_integral():
        return int(decimal_amount)
    return float(decimal_amount)


def _fetch_payment(payment_key):
    if not payment_key:
        return None, None

    try:
        response = requests.get(
            url=f"https://api.tosspayments.com/v1/payments/{payment_key}",
            auth=HTTPBasicAuth(settings.TOSS_SECRET_KEY, ""),
            timeout=20,
        )
    except requests.RequestException as exc:
        return None, ("PAYMENT_LOOKUP_ERROR", f"Не удалось получить статус платежа: {exc}")

    if not response.ok:
        return None, _parse_error(response)

    try:
        return response.json(), None
    except ValueError:
        return None, ("INVALID_PAYMENT_LOOKUP_RESPONSE", "Платёжный шлюз вернул некорректный ответ при запросе статуса.")


def _parse_payment_datetime(raw_value):
    if not raw_value:
        return None

    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None


def _confirmation_window_expired(payment_data):
    requested_at = _parse_payment_datetime(payment_data.get("requestedAt"))
    if requested_at is None:
        return False

    return timezone.now() - requested_at > timedelta(minutes=10)


def _sync_invoice_from_payment(invoice, payment_key, payment_data):
    status = payment_data.get("status", invoice.status)
    invoice.payment_id = payment_data.get("paymentKey", payment_key)
    invoice.status = status
    invoice.is_paid = status == "DONE"
    invoice.save(update_fields=["payment_id", "status", "is_paid", "confirm_response", "updated_at"])


def _serialize_confirm_response(response=None, exc=None):
    if exc is not None:
        payload = {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }
        return json.dumps(payload, ensure_ascii=False)

    if response is None:
        return None

    try:
        body = response.json()
    except ValueError:
        body = response.text or ""

    payload = {
        "status_code": response.status_code,
        "ok": response.ok,
        "body": body,
    }
    return json.dumps(payload, ensure_ascii=False)


def _build_confirm_error_message(default_message, payment_data):
    if not payment_data:
        return default_message

    status = payment_data.get("status")
    if status == "DONE":
        return "Платёж уже подтверждён в Toss Payments."
    if status == "READY":
        return "Покупатель ещё не завершил оплату в платёжном окне."
    if status == "EXPIRED":
        return "Время подтверждения платежа истекло. Нужно создать новый счёт и оплатить его заново."
    if status == "IN_PROGRESS":
        if _confirmation_window_expired(payment_data):
            return "Платёж авторизован, но 10-минутное окно подтверждения уже истекло. Нужно создать новый счёт и оплатить его заново."
        return "Платёж ещё обрабатывается в Toss Payments. Повторите подтверждение через несколько секунд."

    return f"{default_message} Текущий статус платежа в Toss Payments: {status or 'UNKNOWN'}."


def _render_failed(request, invoice, order_id, code, message):
    context = {
        "home_url": _default_home_url(),
        "invoice": invoice,
        "order_id": order_id,
        "error_code": code,
        "error_message": message,
    }
    return render(request, "finance/payment_failed.html", context)


def _render_success(request, invoice, order_id, payment_key, amount):
    context = {
        "home_url": _default_home_url(),
        "invoice": invoice,
        "order_id": order_id,
        "payment_key": payment_key,
        "amount": amount,
    }
    return render(request, "finance/payment_success.html", context)


def _build_missing_confirm_params_message():
    return (
        "Не пришли параметры paymentKey и amount от Toss Payments. "
        "Подтверждение доступно только из successUrl после завершения оплаты."
    )


def _amount_matches_invoice(invoice, confirm_amount):
    try:
        return Decimal(str(invoice.amount)) == Decimal(str(confirm_amount))
    except (InvalidOperation, TypeError, ValueError):
        return False


def confirm_payment(request, invoice_order_id):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    order_id = request.GET.get("orderId") or invoice_order_id
    invoice = InvoiceTossPayments.objects.filter(order_id=order_id).first()
    if not invoice:
        return _render_failed(
            request=request,
            invoice=None,
            order_id=order_id,
            code="INVOICE_NOT_FOUND",
            message="Инвойс для подтверждения не найден.",
        )

    if invoice.is_paid and invoice.status == "DONE":
        return _render_success(
            request=request,
            invoice=invoice,
            order_id=order_id,
            payment_key=invoice.payment_id,
            amount=invoice.amount,
        )

    payment_key = request.GET.get("paymentKey")
    raw_amount = request.GET.get("amount")
    confirm_amount = _normalize_amount(raw_amount, None)

    if not payment_key or raw_amount in (None, "") or confirm_amount is None:
        return _render_failed(
            request=request,
            invoice=invoice,
            order_id=order_id,
            code="MISSING_CONFIRM_PARAMS",
            message=_build_missing_confirm_params_message(),
        )

    if not _amount_matches_invoice(invoice, confirm_amount):
        return _render_failed(
            request=request,
            invoice=invoice,
            order_id=order_id,
            code="AMOUNT_MISMATCH",
            message="Сумма в callback от Toss Payments не совпадает с суммой инвойса.",
        )

    if not (invoice.is_paid and invoice.status == "DONE"):
        try:
            response = None
            for attempt in range(CONFIRM_RETRY_ATTEMPTS):
                response = requests.post(
                    url="https://api.tosspayments.com/v1/payments/confirm",
                    json={
                        "paymentKey": payment_key,
                        "orderId": order_id,
                        "amount": confirm_amount,
                    },
                    auth=HTTPBasicAuth(settings.TOSS_SECRET_KEY, ""),
                    timeout=20,
                )

                if response.ok:
                    break

                error_code, _ = _parse_error(response)
                if error_code not in CONFIRM_RETRYABLE_ERROR_CODES or attempt == CONFIRM_RETRY_ATTEMPTS - 1:
                    break

                time.sleep(CONFIRM_RETRY_DELAY_SECONDS)
        except requests.RequestException as exc:
            invoice.status = "FAILED"
            invoice.is_paid = False
            invoice.confirm_response = _serialize_confirm_response(exc=exc)
            invoice.save(update_fields=["status", "is_paid", "confirm_response", "updated_at"])
            return _render_failed(
                request=request,
                invoice=invoice,
                order_id=order_id,
                code="CONFIRM_REQUEST_ERROR",
                message=f"Ошибка запроса к платёжному шлюзу: {exc}",
            )

        invoice.confirm_response = _serialize_confirm_response(response=response)

        if not response.ok:
            error_code, error_message = _parse_error(response)
            if error_code == "ALREADY_PROCESSED_PAYMENT":
                payment_data, _ = _fetch_payment(payment_key)
                if payment_data:
                    _sync_invoice_from_payment(invoice, payment_key, payment_data)
                else:
                    invoice.payment_id = payment_key
                    invoice.status = "DONE"
                    invoice.is_paid = True
                    invoice.save(update_fields=["payment_id", "status", "is_paid", "confirm_response", "updated_at"])
            else:
                payment_data, lookup_error = _fetch_payment(payment_key)
                if payment_data:
                    _sync_invoice_from_payment(invoice, payment_key, payment_data)
                    if invoice.is_paid:
                        return _render_success(
                            request=request,
                            invoice=invoice,
                            order_id=order_id,
                            payment_key=invoice.payment_id,
                            amount=raw_amount,
                        )

                    error_message = _build_confirm_error_message(error_message, payment_data)
                else:
                    invoice.status = "FAILED"
                    invoice.is_paid = False
                    invoice.save(update_fields=["status", "is_paid", "confirm_response", "updated_at"])
                    if lookup_error:
                        error_message = f"{error_message} Не удалось уточнить статус платежа: {lookup_error[1]}"

                return _render_failed(
                    request=request,
                    invoice=invoice,
                    order_id=order_id,
                    code=error_code,
                    message=error_message,
                )
        else:
            data = response.json()
            invoice.payment_id = data.get("paymentKey", payment_key)
            invoice.status = data.get("status", invoice.status)
            invoice.is_paid = invoice.status == "DONE"
            invoice.save(update_fields=["payment_id", "status", "is_paid", "confirm_response", "updated_at"])

    return _render_success(
        request=request,
        invoice=invoice,
        order_id=order_id,
        payment_key=payment_key,
        amount=raw_amount,
    )


def failed_payment(request, invoice_order_id):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    order_id = request.GET.get("orderId") or invoice_order_id
    invoice = InvoiceTossPayments.objects.filter(order_id=order_id).first()
    error_code = request.GET.get("code", "PAYMENT_FAILED")
    error_message = request.GET.get("message", "Не удалось завершить оплату. Попробуйте ещё раз позже.")
    payment_key = request.GET.get("paymentKey") or (invoice.payment_id if invoice else None)

    if invoice:
        was_paid = bool(invoice.is_paid or invoice.status == "DONE")

        invoice.is_paid = False
        invoice.status = "CANCELED" if error_code in {"PAY_PROCESS_CANCELED", "USER_CANCEL", "PAYMENT_CANCELED"} else "FAILED"
        invoice.save(update_fields=["status", "is_paid", "updated_at"])

        if was_paid and payment_key:
            try:
                cancel_response = requests.post(
                    url=f"https://api.tosspayments.com/v1/payments/{payment_key}/cancel",
                    json={"cancelReason": "User reached fail callback page"},
                    auth=HTTPBasicAuth(settings.TOSS_SECRET_KEY, ""),
                    timeout=20,
                )
            except requests.RequestException as exc:
                error_code = "CANCEL_REQUEST_ERROR"
                error_message = f"{error_message} Ошибка запроса отмены: {exc}"
            else:
                if cancel_response.ok:
                    cancel_data = cancel_response.json()
                    invoice.status = cancel_data.get("status", "CANCELED")
                    invoice.is_paid = False
                    invoice.save(update_fields=["status", "is_paid", "updated_at"])
                else:
                    cancel_code, cancel_message = _parse_error(cancel_response)
                    error_code = f"{error_code} | {cancel_code}"
                    error_message = f"{error_message} Отмена не выполнена: {cancel_message}"

    context = {
        "home_url": _default_home_url(),
        "invoice": invoice,
        "order_id": order_id,
        "error_code": error_code,
        "error_message": error_message,
    }
    return render(request, "finance/payment_failed.html", context)
