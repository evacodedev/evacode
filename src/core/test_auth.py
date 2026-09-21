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
