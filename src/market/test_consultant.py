from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from core.models import CurrencyPair
from market import business_ru_orders
from market.models import (
    Consultant,
    ConsultantClientLookup,
    GoodsModel,
    GroupOfGoods,
    SiteOrder,
    SiteOrderItem,
    SiteOrderPayment,
)

PASSWORD = "StrongPass123"
JPEG = b"\xff\xd8\xff\xe0fake-jpeg"


class ConsultantTestBase(TestCase):
    def setUp(self):
        # 1 USD = 1000 ₩, чтобы суммы в тестах читались глазами.
        CurrencyPair.objects.update_or_create(
            base="KRW",
            quote="USD",
            defaults={"name": "Доллар США", "symbol": "$", "rate": Decimal("0.001"), "sort": 20, "is_active": True},
        )
        category = GroupOfGoods.objects.create(
            id=20, default_order="1", deleted=False, name="Тест", updated="2024-01-01T00:00:00Z"
        )
        self.good = GoodsModel.objects.create(
            id=101,
            title="Тестовый крем",
            description="",
            category=category,
            type="goods",
            stock=5,
            retail_price=20000,
            weight=400,
        )
        self.consultant_user = User.objects.create_user("anna@evacode.co.kr", "anna@evacode.co.kr", PASSWORD)
        self.consultant = Consultant.objects.create(user=self.consultant_user, business_ru_employee_id="777")
        self.token = self._token("anna@evacode.co.kr")

    def _token(self, email):
        response = self.client.post(
            "/api/core/auth/login/",
            data={"email": email, "password": PASSWORD},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["access"]

    def _make_user(self, email, **extra):
        user = User.objects.create_user(email, email, PASSWORD, **extra)
        return user, self._token(email)

    def _auth(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.token}"}

    def _draft_body(self, **overrides):
        body = {
            "client": {
                "first_name": "Ivan Petrov",
                "phone": "+7 900 111-22-33",
                "email": "",
                "country": "Korea",
                "city": "",
                "address": "",
                "postal_code": "",
                "comment": "",
            },
            "cart": [{"id": self.good.id, "quantity": 2}],
            "shipping": {"method": "pickup", "destination": "KR"},
            "display_currency": "USD",
        }
        body.update(overrides)
        return body

    def _create_draft(self, token=None, **overrides):
        response = self.client.post(
            "/api/market/consultant/orders/",
            data=self._draft_body(**overrides),
            content_type="application/json",
            **self._auth(token),
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def _add_payment(self, order_id, amount, currency="USD", proof=True, token=None):
        data = {"amount": amount, "currency": currency}
        if proof:
            data["proof"] = SimpleUploadedFile("pay.jpg", JPEG, content_type="image/jpeg")
        return self.client.post(
            f"/api/market/consultant/orders/{order_id}/payments/", data=data, **self._auth(token)
        )


class ConsultantAccessTests(ConsultantTestBase):
    def test_guest_and_buyer_have_no_access(self):
        self.assertEqual(self.client.get("/api/market/consultant/orders/").status_code, 401)
        _buyer, buyer_token = self._make_user("buyer@example.com")
        response = self.client.get("/api/market/consultant/orders/", **self._auth(buyer_token))
        self.assertEqual(response.status_code, 403)

    def test_disabled_consultant_loses_access_immediately(self):
        self.assertEqual(self.client.get("/api/market/consultant/me/", **self._auth()).status_code, 200)
        self.consultant.is_active = False
        self.consultant.save()
        self.assertEqual(self.client.get("/api/market/consultant/me/", **self._auth()).status_code, 403)

    def test_profile_flag(self):
        me = self.client.get("/api/core/auth/me/", **self._auth()).json()
        self.assertTrue(me["is_consultant"])
        _buyer, buyer_token = self._make_user("buyer@example.com")
        me = self.client.get("/api/core/auth/me/", **self._auth(buyer_token)).json()
        self.assertFalse(me["is_consultant"])

    def test_consultant_sees_only_own_orders(self):
        draft = self._create_draft()
        other_user, other_token = self._make_user("boris@evacode.co.kr")
        Consultant.objects.create(user=other_user, business_ru_employee_id="888")
        listing = self.client.get("/api/market/consultant/orders/", **self._auth(other_token)).json()
        self.assertEqual(listing["results"], [])
        detail = self.client.get(f"/api/market/consultant/orders/{draft['id']}/", **self._auth(other_token))
        self.assertEqual(detail.status_code, 404)
        delete = self.client.delete(f"/api/market/consultant/orders/{draft['id']}/", **self._auth(other_token))
        self.assertEqual(delete.status_code, 404)
        self.assertTrue(SiteOrder.objects.filter(public_id=draft["id"]).exists())


class ConsultantDraftTests(ConsultantTestBase):
    @patch("market.consultant_views.export_consultant_order")
    def test_draft_saved_locally_and_not_sent_to_business_ru(self, export_mock):
        draft = self._create_draft()
        order = SiteOrder.objects.get(public_id=draft["id"])
        self.assertEqual(order.status, SiteOrder.Status.CONSULTANT_DRAFT)
        self.assertEqual(order.consultant, self.consultant)
        self.assertEqual(order.amount_krw, 40000)
        self.assertEqual(order.display_currency, "USD")
        self.assertEqual(order.display_amount, Decimal("40.50"))
        self.assertEqual(order.items.get().price_krw, 20000)
        self.assertEqual(order.business_ru_order_id, "")
        export_mock.assert_not_called()

    def test_update_and_delete_draft(self):
        draft = self._create_draft()
        response = self.client.put(
            f"/api/market/consultant/orders/{draft['id']}/",
            data=self._draft_body(cart=[{"id": self.good.id, "quantity": 1}], display_currency="KRW"),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["amount_krw"], 20000)
        self.assertEqual(SiteOrderItem.objects.filter(order__public_id=draft["id"]).count(), 1)
        response = self.client.delete(f"/api/market/consultant/orders/{draft['id']}/", **self._auth())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SiteOrder.objects.filter(public_id=draft["id"]).exists())

    def test_draft_keeps_business_ru_partner_chosen_in_lookup(self):
        body = self._draft_body()
        draft = self._create_draft(client={**body["client"], "business_ru_partner_id": "754559"})
        detail = self.client.get(f"/api/market/consultant/orders/{draft['id']}/", **self._auth()).json()
        self.assertEqual(detail["client"]["business_ru_partner_id"], "754559")

        self.client.put(
            f"/api/market/consultant/orders/{draft['id']}/",
            data=body,
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(SiteOrder.objects.get(public_id=draft["id"]).business_ru_partner_id, "")

    def test_ems_address_must_be_latin(self):
        response = self.client.post(
            "/api/market/consultant/orders/",
            data=self._draft_body(
                client={
                    "first_name": "Иван Петров",
                    "phone": "+79001112233",
                    "country": "Russia",
                    "city": "Moscow",
                    "address": "Tverskaya 1",
                    "postal_code": "101000",
                },
                shipping={"method": "ems", "destination": "RU"},
            ),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("first_name", response.json()["errors"])

    def test_pickup_name_must_be_latin(self):
        response = self.client.post(
            "/api/market/consultant/orders/",
            data=self._draft_body(
                client={"first_name": "Иван Петров", "phone": "+79001112233"},
                shipping={"method": "pickup"},
            ),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"]["first_name"], "Только латиницей (английскими буквами)")

    def _mark_sent(self, order_id, sent, token=None):
        return self.client.post(
            f"/api/market/consultant/orders/{order_id}/sent/",
            data={"sent": sent},
            content_type="application/json",
            **self._auth(token),
        )

    def test_sent_to_client_and_back_to_drafts(self):
        draft = self._create_draft()
        self.assertIsNone(draft["sent_to_client_at"])

        response = self._mark_sent(draft["id"], True)
        self.assertEqual(response.status_code, 200, response.content)
        sent_at = response.json()["sent_to_client_at"]
        self.assertIsNotNone(sent_at)
        self.assertEqual(self._mark_sent(draft["id"], True).json()["sent_to_client_at"], sent_at)

        response = self._mark_sent(draft["id"], False)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["sent_to_client_at"])

    def test_first_payment_marks_sent_and_blocks_return_to_drafts(self):
        draft = self._create_draft()
        with patch("market.consultant_views._start_export"):
            response = self._add_payment(draft["id"], "10")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertIsNotNone(response.json()["sent_to_client_at"])

        response = self._mark_sent(draft["id"], False)
        self.assertEqual(response.status_code, 409)
        self.assertIsNotNone(SiteOrder.objects.get(public_id=draft["id"]).sent_to_client_at)

    def test_sent_mark_is_own_draft_only(self):
        draft = self._create_draft()
        other_user, other_token = self._make_user("boris@evacode.co.kr")
        Consultant.objects.create(user=other_user, business_ru_employee_id="888")
        self.assertEqual(self._mark_sent(draft["id"], True, token=other_token).status_code, 404)

        SiteOrder.objects.filter(public_id=draft["id"]).update(status=SiteOrder.Status.PAID)
        self.assertEqual(self._mark_sent(draft["id"], True).status_code, 409)

    def test_draft_hidden_from_buyer_orders(self):
        self._create_draft(client={**self._draft_body()["client"], "email": "buyer@example.com"})
        _buyer, buyer_token = self._make_user("buyer@example.com")
        mine = self.client.get("/api/market/orders/mine/", **self._auth(buyer_token)).json()
        self.assertEqual(mine["results"], [])


@patch("market.consultant_views._start_export")
class ConsultantPaymentTests(ConsultantTestBase):
    def test_payment_requires_proof(self, _start):
        draft = self._create_draft()
        response = self._add_payment(draft["id"], "40", proof=False)
        self.assertEqual(response.status_code, 400)
        self.assertIn("proof", response.json()["errors"])

    def test_full_payment_submits(self, start_mock):
        draft = self._create_draft()
        response = self._add_payment(draft["id"], "40")
        self.assertEqual(response.status_code, 201, response.content)
        check = response.json()["check"]
        self.assertEqual(check["paid_krw"], 40000)
        self.assertEqual(check["shortfall_krw"], 0)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"/api/market/consultant/orders/{draft['id']}/submit/", data={}, content_type="application/json", **self._auth()
            )
        self.assertEqual(response.status_code, 202, response.content)
        order = SiteOrder.objects.get(public_id=draft["id"])
        self.assertEqual(order.status, SiteOrder.Status.PAID)
        self.assertEqual(order.underpaid_krw, 0)
        start_mock.assert_called_once_with(order.pk)

    def test_underpaid_order_cannot_be_submitted(self, start_mock):
        draft = self._create_draft()
        # Через неделю курс другой: 1 USD = 950 ₩, клиент заплатил те же 40 $.
        CurrencyPair.objects.filter(quote="USD").update(rate=Decimal("0.0010526316"))
        response = self._add_payment(draft["id"], "40")
        check = response.json()["check"]
        self.assertEqual(check["paid_krw"], 38000)
        self.assertEqual(check["shortfall_krw"], 2000)
        self.assertEqual(check["shortfall_display"], {"amount": "2.50", "currency": "USD"})

        url = f"/api/market/consultant/orders/{draft['id']}/submit/"
        response = self.client.post(url, data={}, content_type="application/json", **self._auth())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "underpaid")

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                url,
                data={"accept_underpaid": True, "reason": "Постоянный клиент, курс сменился"},
                content_type="application/json",
                **self._auth(),
            )
        self.assertEqual(response.status_code, 409)
        order = SiteOrder.objects.get(public_id=draft["id"])
        self.assertEqual(order.status, SiteOrder.Status.CONSULTANT_DRAFT)
        self.assertEqual(order.underpaid_krw, 0)
        start_mock.assert_not_called()

        self._add_payment(draft["id"], "2000", currency="KRW")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, data={}, content_type="application/json", **self._auth())
        self.assertEqual(response.status_code, 202, response.content)
        start_mock.assert_called_once()

    def test_top_up_payment_covers_shortfall(self, _start):
        draft = self._create_draft()
        self._add_payment(draft["id"], "30")
        response = self._add_payment(draft["id"], "10000", currency="KRW")
        check = response.json()["check"]
        self.assertEqual(check["paid_krw"], 40000)
        self.assertEqual(check["shortfall_krw"], 0)

    def test_submitted_order_is_locked(self, _start):
        draft = self._create_draft()
        self._add_payment(draft["id"], "40")
        self.client.post(
            f"/api/market/consultant/orders/{draft['id']}/submit/", data={}, content_type="application/json", **self._auth()
        )
        response = self.client.put(
            f"/api/market/consultant/orders/{draft['id']}/",
            data=self._draft_body(),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self._add_payment(draft["id"], "1").status_code, 409)
        payment_id = SiteOrderPayment.objects.get().pk
        self.assertEqual(self._edit_payment(draft["id"], payment_id, {"amount": "1", "currency": "USD"}).status_code, 409)

    def _edit_payment(self, order_id, payment_id, data):
        return self.client.put(
            f"/api/market/consultant/orders/{order_id}/payments/{payment_id}/",
            data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
            **self._auth(),
        )

    def test_edit_payment_recalculates_at_current_rate_and_keeps_proof(self, _start):
        draft = self._create_draft()
        self._add_payment(draft["id"], "30")
        payment = SiteOrderPayment.objects.get()
        CurrencyPair.objects.filter(quote="USD").update(rate=Decimal("0.0008"))

        response = self._edit_payment(draft["id"], payment.pk, {"amount": "32", "currency": "USD"})

        self.assertEqual(response.status_code, 200, response.content)
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal("32.00"))
        self.assertEqual(payment.amount_krw, 40000)
        self.assertEqual(bytes(payment.proof_data), JPEG)
        self.assertEqual(response.json()["check"]["shortfall_krw"], 0)

    def test_edit_payment_replaces_proof(self, _start):
        draft = self._create_draft()
        self._add_payment(draft["id"], "40")
        payment = SiteOrderPayment.objects.get()
        new_proof = SimpleUploadedFile("new.png", b"\x89PNG-new", content_type="image/png")

        response = self._edit_payment(draft["id"], payment.pk, {"amount": "40", "currency": "USD", "proof": new_proof})

        self.assertEqual(response.status_code, 200, response.content)
        payment.refresh_from_db()
        self.assertEqual(bytes(payment.proof_data), b"\x89PNG-new")
        self.assertEqual(payment.proof_content_type, "image/png")
        self.assertTrue(response.json()["payments"][0]["proof_is_image"])

    def test_payment_already_in_business_ru_is_not_editable(self, _start):
        draft = self._create_draft()
        self._add_payment(draft["id"], "40")
        payment = SiteOrderPayment.objects.get()
        payment.business_ru_payment_id = "555"
        payment.save(update_fields=["business_ru_payment_id"])

        response = self._edit_payment(draft["id"], payment.pk, {"amount": "10", "currency": "USD"})

        self.assertEqual(response.status_code, 409)
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal("40.00"))

    def test_proof_visible_to_owner_and_staff_only(self, _start):
        draft = self._create_draft()
        self._add_payment(draft["id"], "40")
        payment = SiteOrderPayment.objects.get()
        url = f"/api/market/consultant/orders/{draft['id']}/payments/{payment.pk}/proof/"

        response = self.client.get(url, **self._auth())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, JPEG)

        self.assertEqual(self.client.get(url).status_code, 401)
        other_user, other_token = self._make_user("boris@evacode.co.kr")
        Consultant.objects.create(user=other_user, business_ru_employee_id="888")
        self.assertEqual(self.client.get(url, **self._auth(other_token)).status_code, 404)

        User.objects.create_user("admin@evacode.co.kr", "admin@evacode.co.kr", PASSWORD, is_staff=True)
        self.client.login(username="admin@evacode.co.kr", password=PASSWORD)
        self.assertEqual(self.client.get(url).status_code, 200)


NO_BR_MATCHES = {"matches": [], "total": 0, "error": ""}
BR_CARD = {
    "id": "754559",
    "name": "Ольга Ким",
    "phones": ["77011234567"],
    "emails": [],
    "address": "Алматы, Абая 10",
    "orders_count": 3,
    "last_order": {"number": "100500", "date": "01.09.2026"},
    "match": "phone",
}


class ConsultantLookupTests(ConsultantTestBase):
    def setUp(self):
        super().setUp()
        patcher = patch("market.consultant_views.lookup_business_ru", return_value=NO_BR_MATCHES)
        self.br_lookup = patcher.start()
        self.addCleanup(patcher.stop)
        SiteOrder.objects.create(
            status=SiteOrder.Status.PAID,
            first_name="Maria Ivanova",
            phone="+7 (912) 345-67-89",
            phone_digits="79123456789",
            email="maria@example.com",
            country="Russia",
            city="Kazan",
            address="Baumana 1, Apt. 2",
            postal_code="420111",
            shipping_method="ems",
            shipping_destination="RU",
            amount_krw=1000,
            amount_usd=Decimal("1"),
        )

    def _lookup(self, query):
        return self.client.get("/api/market/consultant/clients/lookup/", {"q": query}, **self._auth())

    def test_exact_phone_and_email(self):
        response = self._lookup("+7 912 345 67 89")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["client"]["city"], "Kazan")
        response = self._lookup("MARIA@example.com")
        self.assertEqual(response.json()["client"]["first_name"], "Maria Ivanova")
        self.assertEqual(ConsultantClientLookup.objects.filter(found=True).count(), 2)

    def test_partial_queries_find_nothing(self):
        self.assertEqual(self._lookup("maria").status_code, 400)
        self.assertEqual(self._lookup("912345").status_code, 400)
        self.assertEqual(self._lookup("9123456789").status_code, 404)
        self.assertEqual(self._lookup("maria@example").status_code, 400)

    def test_rate_limited(self):
        ConsultantClientLookup.objects.bulk_create(
            [ConsultantClientLookup(consultant=self.consultant, query="x") for _ in range(30)]
        )
        self.assertEqual(self._lookup("maria@example.com").status_code, 429)

    def test_client_only_in_business_ru(self):
        self.br_lookup.return_value = {"matches": [BR_CARD], "total": 1, "error": ""}
        response = self._lookup("+7 701 123 45 67")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIsNone(response.json()["client"])
        self.assertEqual(response.json()["business_ru"]["matches"][0]["id"], "754559")
        self.br_lookup.assert_called_with("", "77011234567")
        self.assertTrue(ConsultantClientLookup.objects.get().found)

    def test_email_lookup_passes_query_as_typed_to_business_ru(self):
        self._lookup("Maria@Example.com")
        self.br_lookup.assert_called_with("Maria@Example.com", "")

    def test_business_ru_down_is_explained(self):
        self.br_lookup.return_value = {"matches": [], "total": 0, "error": "Система заказов EvaCode не ответила"}
        response = self._lookup("+82 10 1111 2222")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Система заказов EvaCode не ответила", response.json()["error"])


class FakeBusinessRuPartners:
    """Контрагенты BR: телефоны в нормализованном виде, как в поле partnercontactinfo.phone."""

    def __init__(self, partners, contacts, orders=None):
        self.partners = partners
        self.contacts = contacts
        self.orders = orders or {}
        self.calls = []

    def request(self, method, model, params=None):
        params = dict(params or {})
        self.calls.append((method, model, params))
        if model == "partners" and "phone" in params:
            ids = {c["partner_id"] for c in self.contacts if c["contact_info_type_id"] == "1" and c["phone"] == params["phone"]}
            return {"result": [p for p in self.partners if p["id"] in ids]}
        if model == "partners" and "email" in params:
            ids = {c["partner_id"] for c in self.contacts if c["contact_info_type_id"] == "4" and c["contact_info"] == params["email"]}
            return {"result": [p for p in self.partners if p["id"] in ids]}
        if model == "partnercontactinfo":
            return {"result": [c for c in self.contacts if c["partner_id"] == params["partner_id"]]}
        if model == "customerorders":
            rows = self.orders.get(params["partner_id"], [])
            if params.get("count_only"):
                return {"result": {"count": len(rows)}}
            page = int(params.get("page") or 1)
            return {"result": rows[page - 1 : page]}
        return {"result": []}


class BusinessRuClientSearchTests(TestCase):
    def test_phone_variants(self):
        from market.business_ru_clients import phone_variants

        self.assertEqual(phone_variants("79001112233"), ["79001112233", "89001112233"])
        self.assertEqual(phone_variants("89001112233"), ["89001112233", "79001112233"])
        self.assertEqual(phone_variants("9001112233"), ["9001112233", "79001112233", "89001112233"])
        self.assertEqual(phone_variants("821012345678"), ["821012345678", "01012345678"])
        self.assertEqual(phone_variants("01012345678"), ["01012345678", "821012345678"])
        self.assertEqual(phone_variants("998901234567"), ["998901234567"])

    def _fake(self):
        partners = [
            {"id": "1", "name": "Ольга (дубль)", "address_actual": "", "address_legal": ""},
            {"id": "2", "name": "Ольга Ким", "address_actual": "", "address_legal": ""},
            {"id": "3", "name": "Удалённый", "address_actual": "", "address_legal": "", "deleted": True},
        ]
        contacts = [
            {"partner_id": "1", "contact_info_type_id": "1", "contact_info": "87011234567", "phone": "87011234567"},
            {"partner_id": "2", "contact_info_type_id": "1", "contact_info": "+7 701 123 45 67", "phone": "77011234567"},
            {"partner_id": "2", "contact_info_type_id": "4", "contact_info": "olga@example.com", "phone": ""},
            {"partner_id": "3", "contact_info_type_id": "1", "contact_info": "77011234567", "phone": "77011234567"},
        ]
        orders = {"2": [{"number": "10", "date": "01.08.2026 10:00"}, {"number": "11", "date": "01.09.2026 10:00", "delivery_address": "Алматы, Абая 10"}]}
        return FakeBusinessRuPartners(partners, contacts, orders)

    def test_finds_all_phone_formats_and_ranks_best_match_first(self):
        from market.business_ru_clients import find_partner_matches

        matches, total = find_partner_matches(self._fake(), "olga@example.com", "77011234567")

        self.assertEqual(total, 2)
        self.assertEqual([card["id"] for card in matches], ["2", "1"])
        best = matches[0]
        self.assertEqual(best["match"], "email+phone")
        self.assertEqual(best["orders_count"], 2)
        self.assertEqual(best["last_order"], {"number": "11", "date": "01.09.2026"})
        self.assertEqual(best["address"], "Алматы, Абая 10")
        self.assertEqual(matches[1]["match"], "phone")

    def test_partner_has_contact(self):
        from market.business_ru_clients import partner_has_contact

        fake = self._fake()
        self.assertTrue(partner_has_contact(fake, "1", "", "77011234567"))
        self.assertTrue(partner_has_contact(fake, "2", "OLGA@example.com", "1"))
        self.assertFalse(partner_has_contact(fake, "2", "other@example.com", "79990000000"))


class FakeBusinessRu:
    def __init__(self):
        self.calls = []
        self.uploads = []
        self.counter = 0
        self.contacts = {}

    def request(self, method, model, params=None):
        params = dict(params or {})
        self.calls.append((method, model, params))
        if method == "get":
            if model == "partnercontactinfo" and "partner_id" in params:
                return {"result": self.contacts.get(params["partner_id"], [])}
            if model == "paymentin" and params.get("help"):
                return {"result": {"params": {"current_account_id": {}}}}
            if "id" in params:
                return {"result": [{"id": params["id"], "current_account_id": "A1", "number": f"N{params['id']}"}]}
            if model == "currentaccounts":
                return {"result": [{"id": "A1", "currency_id": "5", "name": "Банк KRW"}]}
            if model == "contactinfotypes":
                return {"result": [{"id": "10", "name": "Email"}, {"id": "11", "name": "Телефон"}]}
            return {"result": []}
        if method == "post":
            self.counter += 1
            return {"result": {"id": f"{model}-{self.counter}", "number": str(100 + self.counter)}}
        return {"result": {}}

    def upload_file(self, model_name, document_id, filename, content, content_type):
        self.uploads.append((model_name, document_id, filename, content_type))
        return "F1"

    def posted(self, model):
        return [params for method, name, params in self.calls if method == "post" and name == model]


@override_settings(
    BUSINESS_RU_ORGANIZATION_ID="ORG",
    BUSINESS_RU_EMPLOYEE_ID="1",
    BUSINESS_RU_CONSULTANT_CURRENT_ACCOUNT_ID="A1",
    BUSINESS_RU_PAYMENT_OPERATION_ID="OP",
    BUSINESS_RU_STATUS_ID="273",
    BUSINESS_RU_RESERVATION_STORE_ID="S1",
)
class ConsultantExportTests(ConsultantTestBase):
    def _paid_order(self):
        draft = self._create_draft()
        CurrencyPair.objects.filter(quote="USD").update(rate=Decimal("0.0010526316"))
        self._add_payment(draft["id"], "40")
        order = SiteOrder.objects.get(public_id=draft["id"])
        order.status = SiteOrder.Status.PAID
        order.underpaid_krw = 2000
        order.underpaid_reason = "Курс сменился"
        order.save()
        return order

    def test_export_uses_consultant_and_actual_krw(self):
        order = self._paid_order()
        fake = FakeBusinessRu()
        with patch.object(business_ru_orders, "BusinessRuOrderClient", return_value=fake):
            business_ru_orders.export_paid_order(order)

        order.refresh_from_db()
        self.assertTrue(order.business_ru_order_id)
        self.assertTrue(order.business_ru_reservation_id)
        partner = fake.posted("partners")[0]
        self.assertEqual(partner["responsible_employee_id"], "777")
        customer_order = fake.posted("customerorders")[0]
        self.assertEqual(customer_order["responsible_employee_id"], "777")
        self.assertEqual(customer_order["author_employee_id"], "777")
        self.assertNotIn("payment_type_id", customer_order)
        self.assertEqual(customer_order["status_id"], "241")
        payment = fake.posted("paymentin")[0]
        self.assertEqual(payment["sum"], "38000.00")
        self.assertEqual(payment["current_account_id"], "A1")
        self.assertEqual(payment["responsible_employee_id"], "777")
        link = fake.posted("paymentintodocument")[0]
        self.assertEqual(link["sum"], "38000.00")
        proof_comment = next(params for params in fake.posted("comments") if params["note"].startswith("Фото оплаты"))
        self.assertEqual(proof_comment["model_name"], "paymentin")
        self.assertEqual(proof_comment["document_id"], SiteOrderPayment.objects.get().business_ru_payment_id)
        self.assertEqual(fake.uploads[0][0], "comment")
        self.assertTrue(fake.uploads[0][1].startswith("comments-"))
        self.assertEqual(SiteOrderPayment.objects.get().business_ru_file_id, "F1")
        comments = [params["note"] for params in fake.posted("comments")]
        self.assertTrue(any("Не доплачено: 2000 ₩" in note for note in comments))
        self.assertTrue(any("Показано клиенту: 40.50 USD" in note for note in comments))
        self.assertTrue(all(params["employee_id"] == "777" for params in fake.posted("comments")))
        self.assertFalse(fake.posted("partnercontactinfo")[0].get("contact_info") == "")

    def test_export_uses_partner_chosen_in_lookup(self):
        order = self._paid_order()
        order.business_ru_partner_id = "754559"
        order.save(update_fields=["business_ru_partner_id"])
        fake = FakeBusinessRu()
        fake.contacts["754559"] = [{"contact_info_type_id": "1", "contact_info": "8 900 111 22 33", "phone": "89001112233"}]
        with patch.object(business_ru_orders, "BusinessRuOrderClient", return_value=fake):
            business_ru_orders.export_paid_order(order)

        self.assertEqual(fake.posted("partners"), [])
        self.assertEqual(fake.posted("customerorders")[0]["partner_id"], "754559")

    def test_export_ignores_chosen_partner_without_client_contact(self):
        order = self._paid_order()
        order.business_ru_partner_id = "999"
        order.save(update_fields=["business_ru_partner_id"])
        fake = FakeBusinessRu()
        fake.contacts["999"] = [{"contact_info_type_id": "1", "contact_info": "000", "phone": "70000000000"}]
        with patch.object(business_ru_orders, "BusinessRuOrderClient", return_value=fake):
            business_ru_orders.export_paid_order(order)

        self.assertEqual(len(fake.posted("partners")), 1)
        self.assertNotEqual(fake.posted("customerorders")[0]["partner_id"], "999")

    def test_proof_upload_failure_keeps_export_and_drops_empty_comment(self):
        order = self._paid_order()
        fake = FakeBusinessRu()

        def broken_upload(*args):
            raise business_ru_orders.BusinessRuOrderError("files post: сбой")

        fake.upload_file = broken_upload
        with patch.object(business_ru_orders, "BusinessRuOrderClient", return_value=fake):
            business_ru_orders.export_paid_order(order)

        order.refresh_from_db()
        payment = SiteOrderPayment.objects.get()
        self.assertTrue(order.business_ru_order_id)
        self.assertEqual(payment.business_ru_file_id, "")
        self.assertIn("сбой", payment.business_ru_file_error)
        deleted = [params for method, name, params in fake.calls if method == "delete" and name == "comments"]
        self.assertEqual(len(deleted), 1)
        self.assertTrue(deleted[0]["id"].startswith("comments-"))

    @override_settings(BUSINESS_RU_CURRENT_ACCOUNT_ID="A1")
    def test_paypal_export_keeps_site_employee(self):
        order = SiteOrder.objects.create(
            public_id="PAYPAL01",
            status=SiteOrder.Status.PAID,
            first_name="Maria Ivanova",
            phone="+7 900 555-66-77",
            phone_digits="79005556677",
            email="maria@example.com",
            country="Germany",
            city="Berlin",
            address="Steinbacher Weg 4",
            amount_krw=40000,
            goods_krw=40000,
            amount_usd=Decimal("40.50"),
        )
        SiteOrderItem.objects.create(
            order=order, good=self.good, good_id_snapshot=self.good.id, title=self.good.title,
            quantity=2, price_krw=20000, line_total_krw=40000,
        )
        fake = FakeBusinessRu()
        with patch.object(business_ru_orders, "BusinessRuOrderClient", return_value=fake):
            business_ru_orders.export_paid_order(order)

        partner = fake.posted("partners")[0]
        self.assertNotIn("responsible_employee_id", partner)
        contacts = [params["contact_info"] for params in fake.posted("partnercontactinfo")]
        self.assertIn("maria@example.com", contacts)
        customer_order = fake.posted("customerorders")[0]
        self.assertEqual(customer_order["author_employee_id"], "1")
        self.assertEqual(customer_order["responsible_employee_id"], "1")
        self.assertEqual(len(fake.posted("customerordergoods")), 1)
        payments = fake.posted("paymentin")
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]["sum"], "40000.00")
        self.assertEqual(payments[0]["responsible_employee_id"], "1")
        self.assertEqual(fake.uploads, [])

    @override_settings(BUSINESS_RU_CONSULTANT_CURRENT_ACCOUNT_ID="", BUSINESS_RU_CURRENT_ACCOUNT_ID="A2")
    def test_export_falls_back_to_site_account(self):
        order = self._paid_order()
        fake = FakeBusinessRu()
        with patch.object(business_ru_orders, "BusinessRuOrderClient", return_value=fake):
            business_ru_orders.export_paid_order(order)
        self.assertEqual(fake.posted("paymentin")[0]["current_account_id"], "A2")

    @override_settings(BUSINESS_RU_CONSULTANT_CURRENT_ACCOUNT_ID="", BUSINESS_RU_CURRENT_ACCOUNT_ID="")
    def test_export_refuses_without_consultant_account(self):
        order = self._paid_order()
        with patch.object(business_ru_orders, "BusinessRuOrderClient") as client_cls:
            with self.assertRaises(business_ru_orders.BusinessRuOrderError):
                business_ru_orders.export_paid_order(order)
        client_cls.assert_not_called()

    def test_background_export_records_error(self):
        from market.consultant_views import _export_in_background

        order = self._paid_order()
        with patch("market.consultant_views.export_consultant_order", side_effect=RuntimeError("BR недоступен")):
            with patch("market.consultant_views.send_order_confirmation_email") as send_email:
                with patch("django.db.close_old_connections"):
                    _export_in_background(order.pk)
        order.refresh_from_db()
        self.assertIn("BR недоступен", order.business_ru_error)
        send_email.assert_not_called()

    def test_background_export_emails_client(self):
        from market.consultant_views import _export_in_background

        order = self._paid_order()
        with patch("market.consultant_views.export_consultant_order"):
            with patch("market.consultant_views.send_order_confirmation_email") as send_email:
                with patch("django.db.close_old_connections"):
                    _export_in_background(order.pk)
        send_email.assert_called_once()
        self.assertEqual(send_email.call_args[0][0].pk, order.pk)

    def test_client_email_mentions_consultant_and_display_currency(self):
        from market.order_email import STAGE_PAID, build_client_email

        order = self._paid_order()
        order.business_ru_order_number = "5001"
        _subject, text, html = build_client_email(order, STAGE_PAID)
        self.assertIn("Оплата: прошла (через консультанта)", text)
        self.assertIn("≈ 40.50 USD", text)
        self.assertNotIn("PayPal", text)
        self.assertNotIn("PayPal", html)
