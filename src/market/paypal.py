import requests
from django.conf import settings


class PayPalError(Exception):
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def _api_base():
    mode = (settings.PAYPAL_MODE or "sandbox").lower()
    if mode == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def receipt_url(capture_id: str) -> str:
    if not capture_id:
        return ""
    mode = (settings.PAYPAL_MODE or "sandbox").lower()
    host = "https://www.paypal.com" if mode == "live" else "https://www.sandbox.paypal.com"
    return f"{host}/activity/payment/{capture_id}"


def capture_id_from_payload(capture_data: dict) -> str:
    try:
        return capture_data["purchase_units"][0]["payments"]["captures"][0]["id"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def get_access_token():
    client_id = settings.PAYPAL_CLIENT_ID
    secret = settings.PAYPAL_SECRET
    if not client_id or not secret:
        raise PayPalError("Не заданы PAYPAL_CLIENT_ID / PAYPAL_SECRET")

    response = requests.post(
        f"{_api_base()}/v1/oauth2/token",
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


def _headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def create_order(amount_usd, reference_id, return_url, cancel_url, description="Evacode"):
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
        f"{_api_base()}/v2/checkout/orders",
        json=payload,
        headers=_headers(),
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


def capture_order(paypal_order_id):
    response = requests.post(
        f"{_api_base()}/v2/checkout/orders/{paypal_order_id}/capture",
        headers=_headers(),
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
