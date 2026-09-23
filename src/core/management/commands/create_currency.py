from decimal import Decimal

from django.core.management import BaseCommand

from core.models import Currency


# Сид только для пустой БД. Существующие значения (в т.ч. из админки) не трогаем.
_SEED = (
    {
        "key": "krw-rub-kzt",
        "name": "Воны - Рубли - Тенге",
        "value": Decimal("12.5000"),
    },
    {
        "key": "krw-rub-eur",
        "name": "Воны - Рубли - Евро",
        "value": Decimal("13.0000"),
    },
)


class Command(BaseCommand):
    help = "Создаёт курсы валют, если ключей ещё нет. Не перезаписывает ручные правки."

    def handle(self, *args, **options):
        created_n = 0
        for seed in _SEED:
            _, created = Currency.objects.get_or_create(
                key=seed["key"],
                defaults={
                    "name": seed["name"],
                    "value": seed["value"],
                },
            )
            if created:
                created_n += 1
                self.stdout.write(f"Created {seed['key']} = {seed['value']}")
            else:
                self.stdout.write(f"Kept existing {seed['key']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Exchange rates ready ({created_n} created, {len(_SEED) - created_n} unchanged)"
            )
        )
