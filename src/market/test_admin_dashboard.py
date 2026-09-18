from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from market.models import (
    ApiKzSync,
    GoodsModel,
    GroupOfGoods,
    ProductBrand,
    ProductContent,
    ProductContentAgentSettings,
    SiteOrder,
)


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Маски",
            updated="2024-01-01T00:00:00Z",
        )
        self.brand = ProductBrand.objects.create(slug="ohui")
        self.with_brand = GoodsModel.objects.create(
            id=101,
            title="OHUI Unique Cream XYZ",
            description="x",
            category=self.category,
            type="goods",
            content_brand=self.brand,
        )
        self.no_brand = GoodsModel.objects.create(
            id=102,
            title="Без бренда крем",
            description="",
            category=self.category,
            type="goods",
        )
        ProductContent.objects.create(
            good=self.no_brand,
            enrichment_status="needs_enrichment",
            enrichment_reasons=["empty", "no_ingredients"],
            agent_error="timeout",
            agent_draft={"lead": {"source_url": "https://example.com"}},
        )
        SiteOrder.objects.create(
            status=SiteOrder.Status.PAID,
            first_name="Ivan",
            phone="8210111",
            email="ivan@example.com",
            country="KR",
            city="Seoul",
            address="1",
            amount_krw=15000,
            amount_usd=Decimal("10.00"),
            paid_at=timezone.now(),
            business_ru_error="BR down",
        )
        SiteOrder.objects.create(
            status=SiteOrder.Status.PENDING,
            first_name="Kim",
            phone="8210222",
            email="kim@example.com",
            country="KR",
            city="Seoul",
            address="2",
            amount_krw=5000,
            amount_usd=Decimal("3.00"),
        )
        ApiKzSync.objects.create(
            warehouse_code=ApiKzSync.WAREHOUSE_KZ,
            ok=False,
            store_id="936507",
            inventory_id="2836556",
            inventory_number="2836556",
            prices_updated=0,
            prices_unchanged=10,
            prices_failed=0,
            prices_goods=1,
            message=(
                "склад 936507: остатки 51, API 44, строк описи 51, излишки 0, недостачи 0, "
                "инвентаризация id=2836556 № 2836556 (проведено), оприходование не создано "
                "(нет излишков), списание не создано (нет недостач)"
            ),
        )
        ProductContentAgentSettings.load()

    def test_superuser_sees_dashboard_kpis(self):
        user = User.objects.create_superuser("admin", "a@a.test", "pass")
        self.client.force_login(user)
        response = self.client.get("/admin/")
        self.assertContains(response, "Заказы за сегодня")
        self.assertContains(response, "Очередь контента")
        self.assertContains(response, "Без бренда крем")
        self.assertContains(response, "Оплаченные без выгрузки в Business.ru")
        self.assertContains(response, "Справочник заполняется вручную")
        self.assertContains(response, "Агент контента выключен")
        self.assertContains(response, "Последний синк KZ с ошибкой")
        self.assertContains(response, "Синхронизация KZ")
        self.assertContains(response, "Инвентаризация")
        self.assertContains(response, "Остатки")
        self.assertContains(response, "API KZ")

    def test_staff_without_order_perm_hides_orders(self):
        user = User.objects.create_user("mgr", "m@a.test", "pass", is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename="view_goodsmodel"))
        self.client.force_login(user)
        response = self.client.get("/admin/")
        self.assertNotContains(response, "Заказы за сегодня")
        self.assertContains(response, "Очередь контента")
        self.assertContains(response, "Без бренда крем")

    def test_brand_filter_lists_empty_only(self):
        user = User.objects.create_superuser("admin", "a@a.test", "pass")
        self.client.force_login(user)
        url = reverse("admin:market_goodsmodel_changelist")
        response = self.client.get(url, {"brand_filled": "no"})
        self.assertContains(response, "Без бренда крем")
        self.assertNotContains(response, "OHUI Unique Cream XYZ")
