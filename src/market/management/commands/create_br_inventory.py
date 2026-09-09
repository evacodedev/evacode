from django.core.management.base import BaseCommand, CommandError

from market.br_stock_inventory import (
    BrStockInventoryError,
    create_stock_inventory,
    execute_kz_stock_sync,
)


class Command(BaseCommand):
    help = (
        "Создать инвентаризацию Business.Ru по складу BUSINESS_RU_INVENTORY_STORE_ID: "
        "остатки склада + факт из CRM stock API"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только посчитать строки, документ не создавать",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            try:
                summary = create_stock_inventory(dry_run=True)
            except BrStockInventoryError as exc:
                raise CommandError(str(exc)) from exc
        else:
            result = execute_kz_stock_sync()
            if result.get("busy"):
                raise CommandError(result["message"])
            if not result.get("ok"):
                raise CommandError(result["message"])
            summary = result.get("summary") or {}
        self.stdout.write(
            f"склад id={summary['store_id']} "
            f"остатки={summary['current_lines']} "
            f"api={summary['api_lines']} "
            f"строк описи={summary['inventory_lines']} "
            f"излишки={summary['surplus']} "
            f"недостачи={summary['shortage']} "
            f"совпали={summary['equal']}"
        )
        if summary.get("skipped_unknown_ids"):
            self.stdout.write(
                self.style.WARNING(
                    f"пропущены комплекты: {summary['skipped_unknown_ids']}"
                )
            )
        if summary.get("dry_run"):
            self.stdout.write("dry-run: документ не создан")
            return
        if not summary["inventory_id"]:
            self.stdout.write("нет строк — документ не создан")
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"инвентаризация id={summary['inventory_id']} "
                f"№ {summary['inventory_number'] or '—'} "
                f"{'(проведено)' if summary.get('inventory_held') else '(не проведено)'}"
            )
        )
        if summary.get("posting_id"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"оприходование id={summary['posting_id']} "
                    f"№ {summary['posting_number'] or '—'} "
                    f"{'(проведено)' if summary.get('posting_held') else '(не проведено)'}"
                )
            )
        else:
            self.stdout.write("оприходование не создано: нет излишков")
        if summary.get("charge_id"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"списание id={summary['charge_id']} "
                    f"№ {summary['charge_number'] or '—'} "
                    f"{'(проведено)' if summary.get('charge_held') else '(не проведено)'}"
                )
            )
        else:
            self.stdout.write("списание не создано: нет недостач")
        if summary.get("held_errors"):
            self.stdout.write(self.style.ERROR(f"проводка: {summary['held_errors']}"))
        self.stdout.write(
            f"цены: обновлено={summary.get('prices_updated') or 0} "
            f"без изменений={summary.get('prices_unchanged') or 0} "
            f"ошибок={summary.get('prices_failed') or 0} "
            f"товаров={summary.get('prices_goods') or 0}"
        )
        if summary.get("prices_list_id"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"назначение цен id={summary['prices_list_id']} "
                    f"№ {summary.get('prices_list_number') or '—'}"
                )
            )
