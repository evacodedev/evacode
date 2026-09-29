from contextlib import contextmanager
from datetime import time as dt_time
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from market.br_ru_stock_inventory import run_scheduled_ru_stock_sync
from market.models import ApiRuSync, ApiRuSyncSettings


SUCCESS_SUMMARY = {
    "store_id": "903587",
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
    "inventory_held": True,
    "posting_held": True,
    "charge_held": True,
    "prices_updated": 47,
    "prices_unchanged": 0,
    "prices_failed": 0,
    "prices_goods": 47,
    "prices_list_id": "88",
    "prices_list_number": "PL-1",
}


class ApiRuAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@localhost", "admin")
        self.client.force_login(self.user)

    def test_index_shows_api_ru_group_separate_from_kz(self):
        response = self.client.get("/admin/")
        self.assertContains(response, "API RU")
        self.assertContains(response, "API KZ")
        self.assertContains(response, "История синхронизаций RU")
        self.assertContains(response, "Расписание синхронизации RU")

    def test_changelist_has_sync_button(self):
        response = self.client.get(reverse("admin:market_apirusync_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Запустить сейчас")

    def test_settings_opens_singleton(self):
        response = self.client.get(reverse("admin:market_apirusyncsettings_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Расписание включено")
        self.assertContains(response, "Сейчас на сервере")

    @patch("market.br_ru_stock_inventory.create_ru_stock_inventory")
    def test_sync_appends_history_row(self, mocked):
        mocked.return_value = SUCCESS_SUMMARY
        url = reverse("admin:market_apirusync_sync")
        self.client.post(url, follow=True)
        self.assertEqual(ApiRuSync.objects.count(), 1)
        row = ApiRuSync.objects.get()
        self.assertTrue(row.ok)
        self.assertEqual(row.store_id, "903587")
        self.assertEqual(row.inventory_id, "99")
        self.assertIn("инвентаризация id=99", row.message)
        self.assertIn("цены: обновлено 47", row.message)
        self.assertEqual(row.prices_updated, 47)
        self.assertEqual(row.prices_list_id, "88")

    @patch("market.br_ru_stock_inventory.ru_stock_sync_lock")
    def test_sync_busy_does_not_write_history(self, lock):
        @contextmanager
        def busy():
            yield False

        lock.side_effect = lambda: busy()
        response = self.client.post(reverse("admin:market_apirusync_sync"), follow=True)
        self.assertContains(response, "Синхронизация RU уже выполняется")
        self.assertEqual(ApiRuSync.objects.count(), 0)

    def test_schedule_skips_when_disabled(self):
        ApiRuSyncSettings.load()
        with patch("market.br_ru_stock_inventory.create_ru_stock_inventory") as mocked:
            self.assertIsNone(run_scheduled_ru_stock_sync())
        mocked.assert_not_called()

    @patch("market.br_ru_stock_inventory.create_ru_stock_inventory")
    def test_schedule_runs_when_due(self, mocked):
        mocked.return_value = SUCCESS_SUMMARY
        now = timezone.localtime()
        row = ApiRuSyncSettings.load()
        row.enabled = True
        row.weekdays = str(now.weekday())
        row.run_time = dt_time(0, 0)
        row.save()
        result = run_scheduled_ru_stock_sync(now=now)
        self.assertTrue(result["ok"])
        self.assertEqual(ApiRuSync.objects.count(), 1)
        mocked.assert_called_once()
