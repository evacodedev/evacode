from contextlib import contextmanager
from datetime import time as dt_time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from market.br_stock_inventory import execute_kz_stock_sync, run_scheduled_kz_stock_sync
from market.models import ApiKzSync, ApiKzSyncSettings


SUCCESS_SUMMARY = {
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


class ApiKzAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@localhost", "admin")
        self.client.force_login(self.user)

    def test_index_shows_api_kz_group(self):
        response = self.client.get("/admin/")
        self.assertContains(response, "API KZ")
        self.assertContains(response, "История синхронизаций")
        self.assertContains(response, "Расписание синхронизации")

    def test_changelist_has_sync_button(self):
        response = self.client.get(reverse("admin:market_apikzsync_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "История синхронизаций")
        self.assertContains(response, "Запустить сейчас")

    def test_settings_opens_singleton(self):
        response = self.client.get(reverse("admin:market_apikzsyncsettings_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Расписание включено")
        self.assertContains(response, "Дни недели")
        self.assertContains(response, "Время запуска")
        self.assertContains(response, "Сейчас на сервере")
        self.assertContains(response, "пояс Django:")

    @patch("market.br_stock_inventory.create_stock_inventory")
    def test_sync_appends_history_row(self, mocked):
        mocked.return_value = SUCCESS_SUMMARY
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

    @patch("market.br_stock_inventory.create_stock_inventory")
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

    @patch("market.br_stock_inventory.kz_stock_sync_lock")
    def test_sync_busy_does_not_write_history(self, lock):
        @contextmanager
        def busy():
            yield False

        lock.side_effect = lambda: busy()
        response = self.client.post(reverse("admin:market_apikzsync_sync"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Синхронизация уже выполняется")
        self.assertEqual(ApiKzSync.objects.count(), 0)

    def test_execute_busy_skips_inventory(self):
        with patch("market.br_stock_inventory.kz_stock_sync_lock") as lock:
            @contextmanager
            def busy():
                yield False

            lock.side_effect = lambda: busy()
            with patch("market.br_stock_inventory.create_stock_inventory") as mocked:
                result = execute_kz_stock_sync()
        self.assertTrue(result["busy"])
        mocked.assert_not_called()
        self.assertEqual(ApiKzSync.objects.count(), 0)

    def test_schedule_skips_when_disabled(self):
        ApiKzSyncSettings.load()
        with patch("market.br_stock_inventory.create_stock_inventory") as mocked:
            self.assertIsNone(run_scheduled_kz_stock_sync())
        mocked.assert_not_called()

    @patch("market.br_stock_inventory.create_stock_inventory")
    def test_schedule_runs_when_due(self, mocked):
        mocked.return_value = SUCCESS_SUMMARY
        now = timezone.localtime()
        row = ApiKzSyncSettings.load()
        row.enabled = True
        row.weekdays = str(now.weekday())
        row.run_time = dt_time(0, 0)
        row.save()
        result = run_scheduled_kz_stock_sync(now=now)
        self.assertTrue(result["ok"])
        self.assertEqual(ApiKzSync.objects.count(), 1)
        mocked.assert_called_once()

    @patch("market.br_stock_inventory.create_stock_inventory")
    def test_schedule_uses_last_run_including_manual(self, mocked):
        mocked.return_value = SUCCESS_SUMMARY
        now = timezone.localtime()
        row = ApiKzSyncSettings.load()
        row.enabled = True
        row.weekdays = str(now.weekday())
        row.run_time = dt_time(0, 0)
        row.save()
        ApiKzSync.objects.create(ok=True, message="manual")
        self.assertIsNone(run_scheduled_kz_stock_sync(now=now))
        mocked.assert_not_called()
        later = now + timedelta(days=7)
        result = run_scheduled_kz_stock_sync(now=later)
        self.assertTrue(result["ok"])
        mocked.assert_called_once()
