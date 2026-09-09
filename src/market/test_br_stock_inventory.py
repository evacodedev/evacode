from datetime import datetime

from django.test import SimpleTestCase

from market.br_stock_inventory import (
    BusinessRuOrderError,
    apply_kz_sale_prices,
    collect_kz_sale_price_changes,
    fetch_kz_purchase_prices,
    hold_stock_documents,
    kz_purchase_from_postings,
    kz_sync_is_due,
    merge_inventory_rows,
    parse_crm_catalog,
    parse_crm_products,
    pick_kz_purchase_price,
    shortage_rows,
    store_total,
    surplus_rows,
    sync_result_text,
)


class BrStockInventoryTests(SimpleTestCase):
    def test_parse_crm_products(self):
        qty = parse_crm_products(
            {
                "currency": "KZT",
                "products": [
                    {"external_id": 11, "quantity": 75},
                    {"external_id": "12", "quantity": "3"},
                    {"quantity": 1},
                ],
            }
        )
        self.assertEqual(qty, {11: 75.0, 12: 3.0})

    def test_parse_crm_catalog_prices(self):
        qty, prices = parse_crm_catalog(
            {
                "products": [
                    {
                        "external_id": 1673344,
                        "quantity": 44,
                        "price_wholesale_small": 7722,
                        "price_wholesale_medium": 6006,
                        "price_wholesale_large": 5148,
                        "price_retail": 12000,
                    }
                ]
            }
        )
        self.assertEqual(qty, {1673344: 44.0})
        self.assertEqual(
            prices[1673344],
            {
                "price_wholesale_small": 7722.0,
                "price_wholesale_medium": 6006.0,
                "price_wholesale_large": 5148.0,
                "price_retail": 12000.0,
            },
        )

    def test_collect_kz_sale_price_changes_skips_unchanged(self):
        type_ids = {
            "price_retail": "936503",
            "price_wholesale_small": "1058601",
        }
        current = {
            "936503": {1: 12000},
            "1058601": {1: 100},
        }
        crm = {1: {"price_retail": 12000, "price_wholesale_small": 7722}}
        changes, stats = collect_kz_sale_price_changes(current, crm, type_ids)
        self.assertEqual(stats["prices_unchanged"], 1)
        self.assertEqual(stats["prices_updated"], 1)
        self.assertEqual(changes, {1: [("1058601", 7722.0), ("936503", 12000.0)]})

    def test_apply_kz_sale_prices_writes_all_type_columns(self):
        class FakeClient:
            def __init__(self):
                self.posts = []

            def request(self, method, model, params=None):
                params = params or {}
                if method == "get" and model == "currentprices":
                    type_id = str(params.get("price_type_id"))
                    rows = []
                    if type_id == "936503":
                        rows = [{"good_id": "1", "price": "12000"}]
                    if type_id == "1058601":
                        rows = [{"good_id": "1", "price": "100"}]
                    return {"result": rows}
                if method == "post":
                    self.posts.append((model, params))
                    if model == "salepricelists":
                        return {"result": {"id": "10", "number": "PL-1"}}
                    if model == "salepricelistspricetypes":
                        return {"result": {"id": "11"}}
                    if model == "salepricelistgoods":
                        return {"result": {"id": "20"}}
                    if model == "salepricelistgoodprices":
                        return {"result": {"id": "30"}}
                if method == "put" and model == "salepricelists":
                    self.posts.append((model, params))
                    return {"result": {"id": params.get("id")}}
                raise AssertionError((method, model, params))

        client = FakeClient()
        stats = apply_kz_sale_prices(
            client,
            {1: {"price_retail": 12000, "price_wholesale_small": 7722}},
            {
                "org_id": "1",
                "employee_id": "2",
                "kz_sale_price_type_ids": {
                    "price_retail": "936503",
                    "price_wholesale_small": "1058601",
                    "price_wholesale_medium": "1709914",
                    "price_wholesale_large": "1058605",
                },
            },
        )
        self.assertEqual(stats["prices_unchanged"], 1)
        self.assertEqual(stats["prices_updated"], 1)
        self.assertEqual(stats["prices_list_id"], "10")
        self.assertEqual(stats["prices_list_number"], "PL-1")
        models = [item[0] for item in client.posts]
        self.assertEqual(
            models,
            [
                "salepricelists",
                "salepricelistspricetypes",
                "salepricelistspricetypes",
                "salepricelistspricetypes",
                "salepricelistspricetypes",
                "salepricelistgoods",
                "salepricelistgoodprices",
                "salepricelistgoodprices",
                "salepricelists",
            ],
        )
        created = client.posts[0][1]
        self.assertEqual(created["organization_id"], "1")
        self.assertNotIn("price_type_ids[0]", created)
        type_links = [item[1] for item in client.posts if item[0] == "salepricelistspricetypes"]
        self.assertEqual(
            [row["price_type_id"] for row in type_links],
            ["1058601", "1709914", "1058605", "936503"],
        )
        self.assertEqual(type_links[0]["price_list_id"], "10")
        self.assertEqual(client.posts[-1][1]["held"], 1)
        prices = [item[1] for item in client.posts if item[0] == "salepricelistgoodprices"]
        self.assertEqual(
            [(row["price_type_id"], row["price"]) for row in prices],
            [("1058601", 7722.0), ("936503", 12000.0)],
        )

    def test_store_total_by_id(self):
        remains = [
            {"store": {"id": "75581", "name": "KR"}, "amount": {"total": "9"}},
            {"store": {"id": "2787290", "name": "Тест склад 1"}, "amount": {"total": "4"}},
        ]
        self.assertEqual(store_total(remains, 2787290), 4.0)
        self.assertIsNone(store_total(remains, 1))

    def test_merge_api_is_truth(self):
        rows = merge_inventory_rows(
            {1: 10, 2: 5, 3: 1},
            {1: 12, 2: 5, 4: 7},
        )
        by_id = {row["good_id"]: row for row in rows}
        self.assertEqual(by_id[1]["amount_curr"], 10)
        self.assertEqual(by_id[1]["amount_fact"], 12)
        self.assertEqual(by_id[2]["amount_fact"], 5)
        self.assertEqual(by_id[3]["amount_fact"], 0)
        self.assertEqual(by_id[4]["amount_curr"], 0)
        self.assertEqual(by_id[4]["amount_fact"], 7)
        self.assertNotIn(5, by_id)

    def test_surplus_rows(self):
        rows = merge_inventory_rows({1: 10, 2: 5}, {1: 12, 2: 3, 4: 7})
        surplus = surplus_rows(rows)
        by_id = {row["good_id"]: row["amount"] for row in surplus}
        self.assertEqual(by_id, {1: 2.0, 4: 7.0})

    def test_shortage_rows(self):
        rows = merge_inventory_rows({1: 10, 2: 5}, {1: 12, 2: 3, 4: 7})
        shortage = shortage_rows(rows)
        by_id = {row["good_id"]: row["amount"] for row in shortage}
        self.assertEqual(by_id, {2: 2.0})

    def test_kz_purchase_price_ignores_won_cost(self):
        good = {
            "cost": "5634.77",
            "prices": [
                {
                    "price": "6300",
                    "price_type": {
                        "name": "Закупочная Цена",
                        "currency": {"id": "14", "short_name": "₩"},
                    },
                },
                {
                    "price": "2315.25",
                    "price_type": {
                        "name": "KZ закупка",
                        "currency": {"id": "7", "short_name": "тенге"},
                    },
                },
            ],
        }
        self.assertEqual(pick_kz_purchase_price(good), 2315.25)

    def test_kz_purchase_price_uses_last_history_row(self):
        good = {
            "prices": [
                {
                    "price": "20107",
                    "price_type": {
                        "name": "KZ закупка",
                        "currency": {"id": "7"},
                    },
                },
                {
                    "price": "16170",
                    "price_type": {
                        "name": "KZ закупка",
                        "currency": {"id": "7"},
                    },
                },
            ],
        }
        self.assertEqual(pick_kz_purchase_price(good), 16170.0)

    def test_fetch_kz_purchase_prices_from_currentprices(self):
        class FakeClient:
            def request(self, method, model, params=None):
                self.assertEqual(model, "currentprices")
                return {
                    "result": [
                        {"good_id": "1473983", "price": "16170", "price_type_id": "936485"},
                        {"good_id": "1", "price": "0", "price_type_id": "936485"},
                    ]
                }

            def assertEqual(self, left, right):
                if left != right:
                    raise AssertionError((left, right))

        costs = fetch_kz_purchase_prices(FakeClient(), "936485")
        self.assertEqual(costs, {1473983: 16170.0})

    def test_posting_fallback_uses_latest_held_kzt(self):
        class FakeClient:
            def request(self, method, model, params=None):
                params = params or {}
                if model == "postinggoods":
                    return {
                        "result": [
                            {"id": "1", "posting_id": "old", "price": "20107"},
                            {"id": "9", "posting_id": "draft", "price": "1"},
                            {"id": "5", "posting_id": "new", "price": "16170"},
                        ]
                    }
                if model == "postings":
                    docs = {
                        "old": {"id": "old", "currency_id": "7", "held": True, "date": "21.01.2026 11:51:00 MSK"},
                        "new": {"id": "new", "currency_id": "7", "held": True, "date": "18.05.2026 14:02:38 MSK"},
                        "draft": {"id": "draft", "currency_id": "7", "held": False, "date": "09.09.2026 06:02:00 MSK"},
                    }
                    return {"result": docs[str(params.get("id"))]}
                raise AssertionError(model)

        self.assertEqual(kz_purchase_from_postings(FakeClient(), 1473983), 16170.0)

    def test_hold_stock_documents_posts_held(self):
        class FakeClient:
            def __init__(self):
                self.puts = []

            def request(self, method, model, params=None):
                self.puts.append((method, model, params))
                return {"result": {"id": params.get("id")}}

        client = FakeClient()
        summary = hold_stock_documents(
            client,
            {"posting_id": "77", "charge_id": "55", "inventory_id": "99"},
        )
        self.assertTrue(summary["posting_held"])
        self.assertTrue(summary["charge_held"])
        self.assertTrue(summary["inventory_held"])
        self.assertEqual([item[1] for item in client.puts], ["postings", "charges", "inventories"])
        self.assertTrue(all(item[2].get("held") == 1 for item in client.puts))

    def test_hold_stock_documents_keeps_errors(self):
        class FakeClient:
            def request(self, method, model, params=None):
                if model == "inventories":
                    raise BusinessRuOrderError("already held")
                return {"result": {"id": params.get("id")}}

        summary = hold_stock_documents(FakeClient(), {"posting_id": "77", "inventory_id": "99"})
        self.assertTrue(summary["posting_held"])
        self.assertFalse(summary["inventory_held"])
        self.assertTrue(summary["held_errors"])

    def test_sync_is_due_when_enabled_and_never_run(self):
        now = datetime(2026, 9, 9, 12, 0)
        self.assertTrue(kz_sync_is_due(True, 24, None, now))
        self.assertFalse(kz_sync_is_due(False, 24, None, now))

    def test_sync_is_due_from_last_run(self):
        last = datetime(2026, 9, 8, 12, 0)
        now = datetime(2026, 9, 9, 12, 0)
        self.assertTrue(kz_sync_is_due(True, 24, last, now))
        self.assertFalse(kz_sync_is_due(True, 24, last, datetime(2026, 9, 9, 11, 59)))

    def test_sync_result_text_names_skipped_kits(self):
        text = sync_result_text({"skipped_unknown_ids": [11, 22], "store_id": "936507"})
        self.assertIn("пропущены комплекты id [11, 22]", text)
