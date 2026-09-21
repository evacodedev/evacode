from django.contrib.auth.models import User
from django.test import TestCase


class CustomerAuthApiTests(TestCase):
    def test_register_login_and_profile(self):
        register = self.client.post(
            "/api/core/auth/register/",
            data={
                "email": "Svetlana@example.com",
                "password": "StrongPass123",
                "password2": "StrongPass123",
                "first_name": "Светлана",
            },
            content_type="application/json",
        )
        self.assertEqual(register.status_code, 201, register.content)
        payload = register.json()
        self.assertIn("access", payload)
        self.assertNotIn("password", payload["user"])
        self.assertEqual(payload["user"]["email"], "svetlana@example.com")
        self.assertEqual(payload["user"]["first_name"], "Светлана")
        self.assertTrue(User.objects.filter(username="svetlana@example.com").exists())

        me = self.client.get(
            "/api/core/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {payload['access']}",
        )
        self.assertEqual(me.status_code, 200, me.content)
        self.assertEqual(me.json()["email"], "svetlana@example.com")
        self.assertNotIn("password", me.json())

        login = self.client.post(
            "/api/core/auth/login/",
            data={"email": "svetlana@example.com", "password": "StrongPass123"},
            content_type="application/json",
        )
        self.assertEqual(login.status_code, 200, login.content)
        self.assertIn("access", login.json())

        patch = self.client.patch(
            "/api/core/auth/me/",
            data={"first_name": "Лана", "last_name": "Иванова"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}",
        )
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(patch.json()["first_name"], "Лана")
        self.assertEqual(patch.json()["last_name"], "Иванова")

    def test_profile_extra_fields_and_optional_birth_date(self):
        User.objects.create_user("lana@example.com", "lana@example.com", "StrongPass123")
        login = self.client.post(
            "/api/core/auth/login/",
            data={"email": "lana@example.com", "password": "StrongPass123"},
            content_type="application/json",
        )
        token = login.json()["access"]
        saved = self.client.patch(
            "/api/core/auth/me/",
            data={
                "phone": "+7 987-654-32-10",
                "birth_date": "1990-01-01",
                "whatsapp": "+7 987-654-32-10",
                "telegram": "@svetlana",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(saved.status_code, 200, saved.content)
        body = saved.json()
        self.assertEqual(body["phone"], "+7 987-654-32-10")
        self.assertEqual(body["birth_date"], "1990-01-01")
        self.assertEqual(body["telegram"], "@svetlana")

        cleared = self.client.patch(
            "/api/core/auth/me/",
            data={"birth_date": ""},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(cleared.status_code, 200, cleared.content)
        self.assertIsNone(cleared.json()["birth_date"])

        bad = self.client.patch(
            "/api/core/auth/me/",
            data={"birth_date": "32.13.1990"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(bad.status_code, 400)

    def test_profile_password_change(self):
        User.objects.create_user("pass@example.com", "pass@example.com", "StrongPass123")
        login = self.client.post(
            "/api/core/auth/login/",
            data={"email": "pass@example.com", "password": "StrongPass123"},
            content_type="application/json",
        )
        changed = self.client.patch(
            "/api/core/auth/me/",
            data={
                "current_password": "StrongPass123",
                "password": "NewStrongPass123",
                "password2": "NewStrongPass123",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}",
        )
        self.assertEqual(changed.status_code, 200, changed.content)
        old = self.client.post(
            "/api/core/auth/login/",
            data={"email": "pass@example.com", "password": "StrongPass123"},
            content_type="application/json",
        )
        self.assertEqual(old.status_code, 400)
        fresh = self.client.post(
            "/api/core/auth/login/",
            data={"email": "pass@example.com", "password": "NewStrongPass123"},
            content_type="application/json",
        )
        self.assertEqual(fresh.status_code, 200, fresh.content)

        denied = self.client.patch(
            "/api/core/auth/me/",
            data={"password": "AnotherPass123", "password2": "AnotherPass123"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {fresh.json()['access']}",
        )
        self.assertEqual(denied.status_code, 400)

        wrong = self.client.patch(
            "/api/core/auth/me/",
            data={
                "current_password": "wrong-pass",
                "password": "AnotherPass123",
                "password2": "AnotherPass123",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {fresh.json()['access']}",
        )
        self.assertEqual(wrong.status_code, 400)

    def test_duplicate_email_and_bad_password(self):
        User.objects.create_user("ivan@example.com", "ivan@example.com", "StrongPass123")
        duplicate = self.client.post(
            "/api/core/auth/register/",
            data={
                "email": "ivan@example.com",
                "password": "StrongPass123",
                "password2": "StrongPass123",
            },
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 400)

        mismatch = self.client.post(
            "/api/core/auth/register/",
            data={
                "email": "new@example.com",
                "password": "StrongPass123",
                "password2": "other",
            },
            content_type="application/json",
        )
        self.assertEqual(mismatch.status_code, 400)

        bad_login = self.client.post(
            "/api/core/auth/login/",
            data={"email": "ivan@example.com", "password": "wrong-pass"},
            content_type="application/json",
        )
        self.assertEqual(bad_login.status_code, 400)

    def test_profile_requires_auth(self):
        response = self.client.get("/api/core/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_address_crud_and_isolation(self):
        owner = User.objects.create_user("owner@example.com", "owner@example.com", "StrongPass123")
        other = User.objects.create_user("other@example.com", "other@example.com", "StrongPass123")
        login = self.client.post(
            "/api/core/auth/login/",
            data={"email": "owner@example.com", "password": "StrongPass123"},
            content_type="application/json",
        )
        token = login.json()["access"]
        created = self.client.post(
            "/api/core/auth/addresses/",
            data={
                "country": "Корея",
                "country_code": "KR",
                "city": "Сеул",
                "street": "район Каннам-гу, улица Тхеран-ро",
                "house": "152",
                "apartment": "",
                "postal_code": "06236",
                "comment": "домофон 12",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(created.status_code, 201, created.content)
        address_id = created.json()["id"]
        self.assertEqual(created.json()["city"], "Сеул")
        self.assertEqual(created.json()["country"], "Корея")
        self.assertEqual(created.json()["country_code"], "KR")
        self.assertEqual(created.json()["postal_code"], "06236")

        missing_country = self.client.post(
            "/api/core/auth/addresses/",
            data={
                "city": "Сеул",
                "street": "Тхеран-ро",
                "house": "1",
                "apartment": "2",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(missing_country.status_code, 400, missing_country.content)

        missing_postal = self.client.post(
            "/api/core/auth/addresses/",
            data={
                "country": "Корея",
                "country_code": "KR",
                "city": "Сеул",
                "street": "Тхеран-ро",
                "house": "1",
                "apartment": "",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(missing_postal.status_code, 400, missing_postal.content)

        listed = self.client.get(
            "/api/core/auth/addresses/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(listed.status_code, 200, listed.content)
        self.assertEqual(len(listed.json()), 1)

        patched = self.client.patch(
            f"/api/core/auth/addresses/{address_id}/",
            data={"house": "154"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(patched.status_code, 200, patched.content)
        self.assertEqual(patched.json()["house"], "154")

        other_login = self.client.post(
            "/api/core/auth/login/",
            data={"email": "other@example.com", "password": "StrongPass123"},
            content_type="application/json",
        )
        other_token = other_login.json()["access"]
        denied = self.client.get(
            f"/api/core/auth/addresses/{address_id}/",
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
        )
        self.assertEqual(denied.status_code, 404)

        deleted = self.client.delete(
            f"/api/core/auth/addresses/{address_id}/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(deleted.status_code, 204)
        empty = self.client.get(
            "/api/core/auth/addresses/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(empty.json(), [])
        self.assertFalse(other.account_addresses.exists())
        self.assertFalse(owner.account_addresses.exists())
