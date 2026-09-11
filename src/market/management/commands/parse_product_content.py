from django.core.management.base import BaseCommand, CommandError

from market.models import GoodsModel
from market.product_content import parse_goods_queryset


class Command(BaseCommand):
    help = "Разобрать описание товара на секции или только оценить, достаточно ли текста"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ids",
            help="Список id через запятую. Без флага — товары без контента (или все при --assess-only).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Пересобрать русский контент, даже если карточка уже разобрана",
        )
        parser.add_argument(
            "--assess-only",
            action="store_true",
            help="Только выставить оценку описания, блоки не переписывать",
        )

    def handle(self, *args, **options):
        queryset = GoodsModel.objects.all().order_by("id")
        raw_ids = (options.get("ids") or "").strip()
        if raw_ids:
            ids = []
            for part in raw_ids.split(","):
                part = part.strip()
                if not part:
                    continue
                if not part.isdigit():
                    raise CommandError(f"Некорректный id: {part}")
                ids.append(int(part))
            if not ids:
                raise CommandError("Укажите хотя бы один id")
            queryset = queryset.filter(id__in=ids)
        elif not options["force"] and not options["assess_only"]:
            queryset = queryset.filter(pdp_content__isnull=True)
        stats = parse_goods_queryset(
            queryset,
            force=options["force"],
            assess_only=options["assess_only"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Разобрано: {stats['parsed']}, пропущено: {stats['skipped']}, "
                f"оценено: {stats['assessed']}, нужно обогащение: {stats['needed']}"
            )
        )
