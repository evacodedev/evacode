from django.core.management.base import BaseCommand, CommandError

from market.models import GoodsModel, ProductContentAgentSettings
from market.product_content_agent import (
    AgentConfigError,
    AgentRunError,
    pending_enrichment_queryset,
    run_content_agent,
    save_agent_draft,
)


class Command(BaseCommand):
    help = "Агент: поиск фактов и черновик секций (не пишет в description товара)"

    def add_arguments(self, parser):
        parser.add_argument("--ids", help="id через запятую")
        parser.add_argument(
            "--pending",
            action="store_true",
            help="Товары needs_enrichment, которых агент ещё не касался (в т.ч. новые после синка)",
        )
        parser.add_argument("--limit", type=int, default=10)

    def handle(self, *args, **options):
        settings = ProductContentAgentSettings.load()
        if not settings.enabled:
            raise CommandError("Включите агента в админке: Агент контента")
        raw_ids = (options.get("ids") or "").strip()
        if raw_ids:
            ids = []
            for part in raw_ids.split(","):
                part = part.strip()
                if not part.isdigit():
                    raise CommandError(f"Некорректный id: {part}")
                ids.append(int(part))
            queryset = GoodsModel.objects.filter(id__in=ids).order_by("id")
        elif options["pending"]:
            queryset = pending_enrichment_queryset()
        else:
            raise CommandError("Укажите --ids= или --pending")
        limit = options["limit"]
        if limit:
            queryset = queryset[:limit]
        ok = 0
        failed = 0
        for good in queryset:
            try:
                run_content_agent(good)
                ok += 1
                self.stdout.write(self.style.SUCCESS(f"{good.id}: черновик записан"))
            except (AgentConfigError, AgentRunError) as extra:
                save_agent_draft(good, None, error=str(extra))
                failed += 1
                self.stderr.write(f"{good.id}: {extra}")
        self.stdout.write(f"Готово: {ok}, ошибки: {failed}")
