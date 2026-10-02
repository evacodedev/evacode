from django.contrib.auth.models import User
from django.test import TestCase

from market.models import GoodsModel, GroupOfGoods, WishlistItem


class WishlistApiTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=70,
            default_order="1",
            deleted=False,
            name="Кремы",
            updated="2024-01-01T00:00:00Z",
        )
        self.cream = GoodsModel.objects.create(
            id=701,
            title="Whoo крем",
            description="Плотный крем для сухой кожи",
            category=self.category,
            type="goods",
            stock=4,
            retail_price=12000,
        )
        self.sold_out = GoodsModel.objects.create(
            id=702,
            title="Снят с полки",
            description="Нет в наличии",
            category=self.category,
            type="goods",
            stock=0,
            retail_price=8000,
        )
        self.user = User.objects.create_user("lana@example.com", "lana@example.com", "StrongPass123")
        self.other = User.objects.create_user("other@example.com", "other@example.com", "StrongPass123")
        self.token = self._token("lana@example.com")

    def _token(self, email):
        login = self.client.post(
            "/api/core/auth/login/",
            data={"email": email, "password": "StrongPass123"},
            content_type="application/json",
        )
        self.assertEqual(login.status_code, 200, login.content)
        return login.json()["access"]

    def _auth(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.token}"}

    def test_guest_cannot_read_or_save(self):
        listed = self.client.get("/api/market/wishlist/")
        self.assertEqual(listed.status_code, 401)
        saved = self.client.post(
            "/api/market/wishlist/",
            data={"goods_id": self.cream.id},
            content_type="application/json",
        )
        self.assertEqual(saved.status_code, 401)
        self.assertEqual(WishlistItem.objects.count(), 0)

    def test_save_list_and_remove(self):
        missing = self.client.post(
            "/api/market/wishlist/",
            data={"goods_id": "нет"},
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(missing.status_code, 400, missing.content)

        unknown = self.client.post(
            "/api/market/wishlist/",
            data={"goods_id": 999999},
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(unknown.status_code, 404, unknown.content)

        first = self.client.post(
            "/api/market/wishlist/",
            data={"goods_id": self.cream.id},
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.json()["id"], self.cream.id)
        self.assertEqual(first.json()["title"], "Whoo крем")
        self.assertIn("excerpt", first.json())
        self.assertNotIn("description", first.json())
        self.assertNotIn("wholesale_price", first.json())

        again = self.client.post(
            "/api/market/wishlist/",
            data={"goods_id": self.cream.id},
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(again.status_code, 200, again.content)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)

        second = self.client.post(
            "/api/market/wishlist/",
            data={"goods_id": self.sold_out.id},
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(second.status_code, 201, second.content)

        listed = self.client.get("/api/market/wishlist/", **self._auth())
        self.assertEqual(listed.status_code, 200, listed.content)
        rows = listed.json()
        self.assertIsInstance(rows, list)
        self.assertEqual([row["id"] for row in rows], [self.sold_out.id, self.cream.id])

        other = self.client.get("/api/market/wishlist/", **self._auth(self._token("other@example.com")))
        self.assertEqual(other.json(), [])

        stolen = self.client.delete(
            f"/api/market/wishlist/{self.cream.id}/",
            **self._auth(self._token("other@example.com")),
        )
        self.assertEqual(stolen.status_code, 404, stolen.content)
        self.assertTrue(WishlistItem.objects.filter(user=self.user, goods=self.cream).exists())

        removed = self.client.delete(f"/api/market/wishlist/{self.cream.id}/", **self._auth())
        self.assertEqual(removed.status_code, 204, removed.content)
        left = self.client.get("/api/market/wishlist/", **self._auth())
        self.assertEqual([row["id"] for row in left.json()], [self.sold_out.id])

        missing_row = self.client.delete(f"/api/market/wishlist/{self.cream.id}/", **self._auth())
        self.assertEqual(missing_row.status_code, 404, missing_row.content)
