import time

from django.core.management.base import BaseCommand, CommandError

from market.br_ru_stock_inventory import run_scheduled_ru_stock_sync


class Command(BaseCommand):
    help = (
        "Фоновая синхронизация остатков RU по расписанию из админки. "
        "Пока расписание выключено, команда только ждёт. Ручной запуск — в истории синхронизаций RU."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Проверить расписание один раз и выйти",
        )

    def handle(self, *args, **options):
        once = options["once"]
        while True:
            result = run_scheduled_ru_stock_sync()
            if result is None:
                self.stdout.write("пропуск: расписание RU выключено или слот ещё не наступил")
            elif result.get("busy"):
                self.stdout.write(self.style.WARNING(result["message"]))
            elif result.get("ok"):
                self.stdout.write(self.style.SUCCESS(result["message"]))
            else:
                self.stderr.write(self.style.ERROR(result["message"]))
                if once:
                    raise CommandError(result["message"])
            if once:
                return
            time.sleep(60)
