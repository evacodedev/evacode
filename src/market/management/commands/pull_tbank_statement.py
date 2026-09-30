from django.core.management.base import BaseCommand, CommandError

from market.tbank import TBankError, pull_recent_statement


class Command(BaseCommand):
    help = "Забрать выписку Т-Банка и сверить входящие платежи с заказами"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14, help="Сколько дней назад смотреть")

    def handle(self, *args, **options):
        try:
            saved = pull_recent_statement(days=options["days"])
        except TBankError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Операций в выписке: {saved}"))
