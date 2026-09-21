import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PayPalError(Exception):
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def normalize_mode(mode=None) -> str:
    value = (mode or getattr(settings, "PAYPAL_MODE", "") or "live").strip().lower()
    return "live" if value == "live" else "sandbox"


def sandbox_tester_emails() -> set[str]:
    raw = getattr(settings, "PAYPAL_SANDBOX_EMAILS", "") or ""
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def user_uses_paypal_sandbox(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not (user.is_staff or user.is_superuser):
        return False
    identity = (getattr(user, "email", None) or getattr(user, "username", None) or "").strip().lower()
    return bool(identity) and identity in sandbox_tester_emails()


def credentials_for_mode(mode: str) -> tuple[str, str]:
    mode = normalize_mode(mode)
    default_mode = normalize_mode()
    if mode == "sandbox":
        client_id = getattr(settings, "PAYPAL_SANDBOX_CLIENT_ID", "") or (
            settings.PAYPAL_CLIENT_ID if default_mode == "sandbox" else ""
        )
        secret = getattr(settings, "PAYPAL_SANDBOX_SECRET", "") or (
            settings.PAYPAL_SECRET if default_mode == "sandbox" else ""
        )
        return client_id, secret
    client_id = settings.PAYPAL_CLIENT_ID if default_mode == "live" else ""
    secret = settings.PAYPAL_SECRET if default_mode == "live" else ""
    return client_id, secret


def sandbox_credentials_ready() -> bool:
    client_id, secret = credentials_for_mode("sandbox")
    return bool(client_id and secret)


def resolve_paypal_mode(user=None, stored_mode=None) -> str:
    if stored_mode:
        return normalize_mode(stored_mode)
    default_mode = normalize_mode()
    if default_mode == "sandbox":
        return "sandbox"
    if user_uses_paypal_sandbox(user) and sandbox_credentials_ready():
        return "sandbox"
    if user_uses_paypal_sandbox(user):
        logger.warning("PayPal sandbox requested for %s, but sandbox keys are empty", getattr(user, "email", ""))
    return "live"


def _api_base(mode=None):
    if normalize_mode(mode) == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def receipt_url(capture_id: str, mode=None) -> str:
    if not capture_id:
        return ""
    host = "https://www.paypal.com" if normalize_mode(mode) == "live" else "https://www.sandbox.paypal.com"
    return f"{host}/activity/payment/{capture_id}"


def capture_id_from_payload(capture_data: dict) -> str:
    try:
        return capture_data["purchase_units"][0]["payments"]["captures"][0]["id"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def get_access_token(mode=None):
    client_id, secret = credentials_for_mode(mode)
    if not client_id or not secret:
        raise PayPalError("Не заданы ключи PayPal для режима %s" % normalize_mode(mode))

    response = requests.post(
        f"{_api_base(mode)}/v1/oauth2/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, secret),
        timeout=20,
    )
    if not response.ok:
        raise PayPalError(
            f"PayPal token error {response.status_code}: {response.text}",
            status_code=response.status_code,
            payload=response.text,
        )
    return response.json()["access_token"]


def _headers(mode=None):
    return {
        "Authorization": f"Bearer {get_access_token(mode)}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def create_order(amount_usd, reference_id, return_url, cancel_url, description="Evacode", mode=None):
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": str(reference_id)[:127],
                "description": (description or "Evacode")[:127],
                "amount": {
                    "currency_code": "USD",
                    "value": f"{amount_usd:.2f}",
                },
            }
        ],
        # Orders v2 has no SOLUTIONTYPE; BILLING is the guest/card landing (classic Sole).
        "application_context": {
            "brand_name": "Evacode",
            "landing_page": "BILLING",
            "user_action": "PAY_NOW",
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
    }
    response = requests.post(
        f"{_api_base(mode)}/v2/checkout/orders",
        json=payload,
        headers=_headers(mode),
        timeout=20,
    )
    if not response.ok:
        raise PayPalError(
            f"PayPal create order error {response.status_code}: {response.text}",
            status_code=response.status_code,
            payload=response.text,
        )
    data = response.json()
    approve_url = next(
        (link.get("href") for link in data.get("links", []) if link.get("rel") == "approve"),
        None,
    )
    if not approve_url:
        raise PayPalError("PayPal не вернул ссылку на оплату", payload=data)
    return data, approve_url


def capture_order(paypal_order_id, mode=None):
    response = requests.post(
        f"{_api_base(mode)}/v2/checkout/orders/{paypal_order_id}/capture",
        headers=_headers(mode),
        timeout=20,
    )
    if not response.ok:
        raise PayPalError(
            f"PayPal capture error {response.status_code}: {response.text}",
            status_code=response.status_code,
            payload=response.text,
        )
    return response.json()


def approval_url_from_order(paypal_order):
    return next(
        (link.get("href") for link in paypal_order.get("links", []) if link.get("rel") == "approve"),
        None,
    )
