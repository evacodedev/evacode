from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from market.models import ApiKzSync


class ApiKzAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@localhost", "admin")
        self.client.force_login(self.user)

    def test_index_shows_api_kz_group(self):
        response = self.client.get("/admin/")
        self.assertContains(response, "API KZ")
        self.assertContains(response, "История синхронизаций")

    def test_changelist_has_sync_button(self):
        response = self.client.get(reverse("admin:market_apikzsync_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "История синхронизаций")
        self.assertContains(response, "Синхронизировать остатки")

    @patch("market.admin.create_stock_inventory")
    def test_sync_appends_history_row(self, mocked):
        mocked.return_value = {
            "warehouse_code": "KZ",
            "store_id": "2787290",
            "current_lines": 1,
            "api_lines": 2,
            "inventory_lines": 2,
            "surplus": 1,
            "shortage": 0,
            "inventory_id": "99",
            "inventory_number": "INV-1",
            "posting_id": "77",
            "posting_number": "POST-1",
            "charge_id": "55",
            "charge_number": "CH-1",
            "skipped_unknown_ids": [],
            "skipped_posting_ids": [],
            "skipped_charge_ids": [],
            "prices_updated": 4,
            "prices_unchanged": 10,
            "prices_failed": 0,
            "prices_goods": 1,
            "prices_list_id": "88",
            "prices_list_number": "PL-9",
            "inventory_held": True,
            "posting_held": True,
            "charge_held": True,
        }
        url = reverse("admin:market_apikzsync_sync")
        first = self.client.post(url, follow=True)
        second = self.client.post(url, follow=True)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(ApiKzSync.objects.count(), 2)
        rows = list(ApiKzSync.objects.order_by("id"))
        self.assertTrue(all(row.ok for row in rows))
        self.assertTrue(all(row.warehouse_code == "KZ" for row in rows))
        self.assertEqual(rows[-1].inventory_id, "99")
        self.assertEqual(rows[-1].posting_id, "77")
        self.assertEqual(rows[-1].charge_id, "55")
        self.assertIn("инвентаризация id=99", rows[-1].message)
        self.assertIn("оприходование id=77", rows[-1].message)
        self.assertIn("списание id=55", rows[-1].message)
        self.assertIn("(проведено)", rows[-1].message)
        self.assertEqual(rows[-1].prices_updated, 4)
        self.assertEqual(rows[-1].prices_unchanged, 10)
        self.assertEqual(rows[-1].prices_list_id, "88")
        self.assertIn("цены: обновлено 4", rows[-1].message)
        self.assertIn("назначение цен id=88", rows[-1].message)

    @patch("market.admin.create_stock_inventory")
    def test_sync_without_document_is_error(self, mocked):
        mocked.return_value = {
            "warehouse_code": "KZ",
            "store_id": "2787290",
            "current_lines": 0,
            "api_lines": 0,
            "inventory_lines": 0,
            "surplus": 0,
            "shortage": 0,
            "inventory_id": None,
            "inventory_number": None,
            "skipped_unknown_ids": [],
        }
        self.client.post(reverse("admin:market_apikzsync_sync"), follow=True)
        self.assertEqual(ApiKzSync.objects.count(), 1)
        obj = ApiKzSync.objects.get()
        self.assertFalse(obj.ok)
        self.assertEqual(obj.inventory_id, "")
        self.assertIn("Документ инвентаризации не создан", obj.message)
