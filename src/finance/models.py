from django.db import models
from yookassa import Configuration, Payment
from django.conf import settings
import uuid
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin
from django.urls import reverse


Configuration.configure(settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_API_TOKEN)

# Create your models here.
class InvoiceYookassa(models.Model):
    payment_id = models.CharField(max_length=100, unique=True, verbose_name="ID Транзакции", blank=True, null=True)
    status = models.CharField(max_length=20, verbose_name="Статус", blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма транзакции")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    customer_name = models.CharField(max_length=128, verbose_name="Имя пользователя/покупателя", default="Имя")
    customer_phone = models.CharField(max_length=64, verbose_name="Номер телефона пользователя/покупателя", default="Телефон")
    customer_email = models.CharField(max_length=64, verbose_name="Почта пользоавтеля/покупателя", default="customer_email@example.com")
    is_paid = models.BooleanField(blank=True, null=True, default=False)
    payment_link = models.TextField(verbose_name="Ссылка на оплату")
    manager_name = models.CharField(max_length=64, verbose_name="Имя менеджера")

    def save(self, *args, **kwargs):

        print(self.customer_name, self.customer_email, self.customer_phone)
        payment = Payment.create(
            {
                "amount": {
                    "value": self.amount,
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://merchant-site.ru/return_url"
                },
                "capture": True,
                "description": self.description,
                "receipt": {
                    "customer": {
                        "full_name": self.customer_name,
                        "email": self.customer_email,
                        # "phone": self.customer_phone,
                    },
                    "items": [
                        {
                            "description": self.description,
                            "amount": {
                                "value": self.amount,
                                "currency": "RUB"
                            },
                            "quantity": 1,
                            "vat_code": "2",
                            "payment_mode": "full_payment",
                            "country_of_origin_code": "CN",
                            "supplier": {
                                "name": self.manager_name,
                            }
                        },
                    ]
                }
            }
        )
        self.payment_link = payment.confirmation.confirmation_url
        super().save(*args, **kwargs)








class InvoiceTossPayments(models.Model):
    class PaymentType(models.TextChoices):
        CARD = "CARD", "Оплата корейской картой"
        FOREIGN = "FOREIGN_EASY_PAY", "Оплата иностранными картами"


    payment_id = models.CharField(max_length=100, unique=True, verbose_name="ID Транзакции", blank=True, null=True)
    status = models.CharField(max_length=20, verbose_name="Статус", blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма транзакции")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    customer_name = models.CharField(max_length=128, verbose_name="Имя пользователя/покупателя", default="Имя")
    customer_phone = models.CharField(max_length=64, verbose_name="Номер телефона пользователя/покупателя", default="Телефон")
    customer_email = models.CharField(max_length=64, verbose_name="Почта пользоавтеля/покупателя", default="customer_email@example.com")
    is_paid = models.BooleanField(blank=True, null=True, default=False)
    payment_link = models.TextField(verbose_name="Ссылка на оплату")
    payment_type = models.CharField(max_length=16, choices=PaymentType.choices, default=PaymentType.CARD, db_index=True)
    manager_name = models.CharField(max_length=64, verbose_name="Имя менеджера")
    order_id = models.CharField(max_length=64, verbose_name="Order ID", blank=True)
    manager_link = models.CharField(max_length=128, verbose_name="Ссылка на контакт менеджера", null=True, blank=True)
    payload = models.TextField(verbose_name="Payload field", blank=True, null=True)
    confirm_response = models.TextField(verbose_name="Confirm response field", blank=True, null=True)

    def _build_toss_payload(self, order_id, success_url, fail_url):
        payload = {
            "method": self.payment_type,
            "amount": int(self.amount),
            "orderId": order_id,
            "orderName": (self.description or "Invoice")[:100],
            "successUrl": success_url,
            "failUrl": fail_url,
        }

        if self.payment_type == self.PaymentType.CARD:
            return payload

        if self.payment_type == self.PaymentType.FOREIGN:
            payload["provider"] = "PAYPAL"
            payload["currency"] = "USD"
            return payload

        raise ValueError(f"Unsupported TOSS payment type: {self.payment_type}")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        request_suffix = uuid.uuid4().hex[:8]
        order_id = f"inv-{self.pk}-{request_suffix}"
        idempotency_key = f"inv-create-{self.pk}-{request_suffix}"

        success_path = reverse("payment_success", kwargs={"invoice_order_id": order_id})
        fail_path = reverse("payment_failed", kwargs={"invoice_order_id": order_id})

        base_url = settings.BACKEND_PUBLIC_URL.strip()
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"
        base_url = base_url.rstrip("/") + "/"

        success_url = urljoin(base_url, success_path.lstrip("/"))
        fail_url = urljoin(base_url, fail_path.lstrip("/"))

        if self.payment_link:
            return

        payload = self._build_toss_payload(
            order_id=order_id,
            success_url=success_url,
            fail_url=fail_url,
        )
        
        self.payload = str(payload)

        headers = {
            "Accept-Language": "en-US",
            "Idempotency-Key": idempotency_key,
        }

        r = requests.post(
            url="https://api.tosspayments.com/v1/payments",
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(settings.TOSS_SECRET_KEY, ""),
            timeout=20
        )
        if not r.ok:
            raise RuntimeError(f"TOSS ERROR {r.status_code} - {r.text}")

        data = r.json()
        self.payment_id = data["paymentKey"]
        self.status = data["status"]
        self.payment_link = data["checkout"]["url"]
        self.order_id = order_id

        super().save(update_fields=["payment_id", "status", "payment_link", "updated_at", "order_id", "payload"])
        
        # super().save(*args, **kwargs)
    # def save(self, *args, **kwargs):
    #     creating = self.pk is None

    #     # 1) сначала сохраняем, чтобы был pk и можно было стабильно сделать orderId
    #     super().save(*args, **kwargs)

    #     # 2) не создаём платёж повторно, если ссылка уже есть
    #     if self.payment_link:
    #         return

    #     url = "https://api.tosspayments.com/v1/payments"

    #     order_id = f"inv-{self.pk}"  # стабильный orderId (важно)
    #     payload = {
    #         "method": "CARD",
    #         "amount": int(self.amount),
    #         "orderId": order_id,
    #         "orderName": (self.description or "Invoice")[:100],
    #         "successUrl": "google.com",  # https://your-domain.com/payments/toss/success
    #         "failUrl": "google.com",        # https://your-domain.com/payments/toss/fail
    #     }

    #     headers = {
    #         "Accept-Language": "en-US",
    #         "Idempotency-Key": f"inv-create-{self.pk}",  # тоже стабильный
    #     }

    #     r = requests.post(
    #         url,
    #         json=payload,
    #         headers=headers,
    #         auth=HTTPBasicAuth(TOSS_SECRET_KEY, ""),
    #         timeout=20
    #     )

    #     # полезно для диагностики
    #     if not r.ok:
    #         raise RuntimeError(f"Toss error {r.status_code}: {r.text}")

    #     data = r.json()
    #     self.payment_link = data["checkout"]["url"]

    #     # 3) сохраняем только поле ссылки, чтобы не уйти в рекурсию/повторное создание
    #     super().save(update_fields=["payment_link"])



    
    


# class PaymentLog(models.Model):
#     payment_id = models.CharField(max_length=100, unique=True)
#     status = models.CharField(max_length=20)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     is_paid = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Payment {self.payment_id} - {self.status}"
