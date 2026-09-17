from django.core.management.base import BaseCommand

from market.brand_cleanup import cleanup_product_brands


class Command(BaseCommand):
    help = "Перевесить товары на канонический бренд и убрать дубли из справочника"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать план, ничего не писать",
        )

    def handle(self, *args, **options):
        stats = cleanup_product_brands(dry_run=options["dry_run"])
        prefix = "план: " if options["dry_run"] else ""
        for source, target, count in stats["moved"]:
            self.stdout.write(f"{prefix}{source} → {target} ({count} тов.)")
        for old_slug, new_slug in stats["renamed"]:
            self.stdout.write(f"{prefix}slug {old_slug} → {new_slug}")
        for slug, old_name, new_name in stats["named"]:
            self.stdout.write(f"{prefix}имя {slug}: {old_name} → {new_name}")
        for slug in stats["missing_target"]:
            self.stderr.write(f"нет канона для {slug}")
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}слито: {len(stats['moved'])}, удалено: {len(stats['deleted'])}, "
                f"без обработки: {len(stats['leftover'])}"
            )
        )
        for brand in stats["leftover"]:
            self.stdout.write(f"без обработки\t{brand.id}\t{brand.slug}\t{brand}")
