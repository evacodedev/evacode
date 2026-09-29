from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from market.br_ru_stock_inventory import (
    apply_ru_sale_prices,
    collect_ru_sale_price_changes,
    create_ru_stock_inventory,
    parse_ru_catalog,
    parse_ru_stock,
    ru_sync_result_text,
)
from market.br_stock_inventory import merge_inventory_rows


class RuStockInventoryTests(SimpleTestCase):
    def test_parse_ru_stock_keeps_zero_quantity(self):
        qty = parse_ru_stock(
            {
                "currency": "RUB",
                "products": [
                    {"external_id": "1001134", "quantity": 1469, "price_retail": 1575},
                    {"external_id": 11, "quantity": 0},
                    {"quantity": 5},
                ],
            }
        )
        self.assertEqual(qty, {1001134: 1469.0, 11: 0.0})

    def test_parse_ru_catalog_keeps_only_incoming_prices(self):
        qty, prices = parse_ru_catalog(
            {
                "products": [
                    {"external_id": 11, "quantity": 2, "price_retail": 1575},
                    {
                        "external_id": 12,
                        "quantity": 1,
                        "price_retail": 2000,
                        "price_wholesale_small": 1800,
                    },
                ]
            }
        )
        self.assertEqual(qty[11], 2.0)
        self.assertEqual(prices[11], {"price_retail": 1575.0})
        self.assertEqual(
            prices[12],
            {"price_retail": 2000.0, "price_wholesale_small": 1800.0},
        )

    def test_collect_updates_only_fields_from_api(self):
        type_ids = {
            "price_retail": "913538",
            "price_wholesale_small": "976958",
        }
        current = {
            "913538": {11: 1000},
            "976958": {11: 800},
        }
        api = {11: {"price_retail": 1575}}
        changes, stats = collect_ru_sale_price_changes(current, api, type_ids)
        self.assertEqual(stats["prices_updated"], 1)
        self.assertEqual(changes, {11: [("913538", 1575.0)]})

    def test_apply_posts_only_retail_column(self):
        client = MagicMock()
        client.request.side_effect = [
            {"result": {"id": "88", "number": "PL-1"}},
            {"result": {"id": "pt"}},
            {"result": {"id": "line"}},
            {"result": {"id": "price"}},
            {"result": {"id": "88"}},
        ]
        cfg = {
            "org_id": "1",
            "employee_id": "2",
            "sale_price_type_ids": {
                "price_retail": "913538",
                "price_wholesale_small": "976958",
            },
        }
        with patch(
            "market.br_ru_stock_inventory.fetch_kz_purchase_prices",
            return_value={},
        ):
            stats = apply_ru_sale_prices(client, {11: {"price_retail": 1575}}, cfg)
        models = [call.args[1] for call in client.request.call_args_list]
        self.assertEqual(models.count("salepricelistspricetypes"), 1)
        type_payload = client.request.call_args_list[1].args[2]
        self.assertEqual(type_payload["price_type_id"], "913538")
        self.assertEqual(stats["prices_list_id"], "88")

    def test_zero_api_qty_writes_off_br_stock(self):
        rows = merge_inventory_rows({11: 4.0}, {11: 0.0})
        self.assertEqual(rows, [{"good_id": 11, "amount_curr": 4.0, "amount_fact": 0.0}])

    def test_result_text_includes_prices(self):
        text = ru_sync_result_text(
            {
                "store_id": "903587",
                "current_lines": 2,
                "api_lines": 47,
                "inventory_lines": 3,
                "surplus": 1,
                "shortage": 1,
                "inventory_id": "99",
                "inventory_number": "INV-1",
                "inventory_held": True,
                "posting_id": "77",
                "posting_number": "POST-1",
                "posting_held": True,
                "charge_id": "55",
                "charge_number": "CH-1",
                "charge_held": True,
                "prices_updated": 47,
                "prices_unchanged": 0,
                "prices_failed": 0,
                "prices_goods": 47,
                "prices_list_id": "88",
            }
        )
        self.assertIn("склад 903587", text)
        self.assertIn("цены: обновлено 47", text)
        self.assertIn("назначение цен id=88", text)

    @override_settings(BUSINESS_RU_ORGANIZATION_ID="1", BUSINESS_RU_EMPLOYEE_ID="2")
    @patch.dict(
        "os.environ",
        {
            "RU_STOCK_USER": "api",
            "RU_STOCK_PASSWORD": "secret",
            "BUSINESS_RU_ORGANIZATION_ID": "1",
            "BUSINESS_RU_EMPLOYEE_ID": "2",
        },
        clear=False,
    )
    @patch("market.br_ru_stock_inventory.apply_ru_sale_prices", return_value={})
    @patch("market.br_ru_stock_inventory.fetch_kz_purchase_prices", return_value={11: 100.0})
    @patch("market.br_ru_stock_inventory.fetch_ru_catalog", return_value=({11: 2.0}, {11: {"price_retail": 1575}}))
    @patch("market.br_ru_stock_inventory.fetch_store_snapshot", return_value=({11: 1.0}, {}))
    def test_dry_run_does_not_post_documents(self, *_mocks):
        client = MagicMock()
        summary = create_ru_stock_inventory(client=client, dry_run=True)
        self.assertEqual(summary["store_id"], "903587")
        self.assertEqual(summary["inventory_lines"], 1)
        client.request.assert_not_called()

    @override_settings(BUSINESS_RU_ORGANIZATION_ID="1", BUSINESS_RU_EMPLOYEE_ID="2")
    @patch.dict(
        "os.environ",
        {
            "RU_STOCK_USER": "api",
            "RU_STOCK_PASSWORD": "secret",
            "BUSINESS_RU_ORGANIZATION_ID": "1",
            "BUSINESS_RU_EMPLOYEE_ID": "2",
        },
        clear=False,
    )
    @patch("market.br_ru_stock_inventory.apply_ru_sale_prices", return_value={"prices_updated": 1, "prices_list_id": "88"})
    @patch("market.br_ru_stock_inventory.hold_stock_documents")
    @patch("market.br_ru_stock_inventory._create_adjustment_document")
    @patch("market.br_ru_stock_inventory.fetch_kz_purchase_prices", return_value={11: 100.0})
    @patch("market.br_ru_stock_inventory.fetch_ru_catalog", return_value=({11: 2.0}, {11: {"price_retail": 1575}}))
    @patch("market.br_ru_stock_inventory.fetch_store_snapshot", return_value=({11: 1.0}, {}))
    def test_live_run_applies_sale_prices(self, snapshot, catalog, costs, adjust, hold, apply_prices):
        client = MagicMock()
        client.request.side_effect = [
            {"result": {"id": "99", "number": "INV-1"}},
            {"result": {"id": "1"}},
        ]
        summary = create_ru_stock_inventory(client=client, dry_run=False)
        apply_prices.assert_called_once()
        self.assertEqual(summary["prices_list_id"], "88")
        self.assertEqual(summary["inventory_id"], "99")
