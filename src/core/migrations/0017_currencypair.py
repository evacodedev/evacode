# Generated manually for CurrencyPair (stage A)

from decimal import Decimal

from django.db import migrations, models


def seed_pairs(apps, schema_editor):
    CurrencyPair = apps.get_model("core", "CurrencyPair")
    seeds = (
        ("RUB", "Российский рубль", "₽", Decimal("0.0740779221"), 10),
        ("USD", "Доллар США", "$", Decimal("0.0008831169"), 20),
        ("EUR", "Евро", "€", Decimal("0.0007662338"), 30),
        ("KZT", "Казахстанский тенге", "₸", Decimal("0.3927922078"), 40),
        ("KGS", "Киргизский сом", "сом", Decimal("0.0766753247"), 50),
        ("UZS", "Узбекский сум", "сум", Decimal("10.3770129870"), 60),
    )
    for quote, name, symbol, rate, sort in seeds:
        CurrencyPair.objects.get_or_create(
            base="KRW",
            quote=quote,
            defaults={
                "name": name,
                "symbol": symbol,
                "rate": rate,
                "sort": sort,
                "is_active": True,
            },
        )


def unseed_pairs(apps, schema_editor):
    CurrencyPair = apps.get_model("core", "CurrencyPair")
    CurrencyPair.objects.filter(base="KRW").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_promote_vadim_admin"),
    ]

    operations = [
        migrations.CreateModel(
            name="CurrencyPair",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("base", models.CharField(default="KRW", max_length=3, verbose_name="База")),
                ("quote", models.CharField(max_length=3, verbose_name="Котировка")),
                ("name", models.CharField(blank=True, max_length=64, verbose_name="Название")),
                ("symbol", models.CharField(blank=True, max_length=8, verbose_name="Символ")),
                ("rate", models.DecimalField(decimal_places=10, max_digits=18, verbose_name="Курс (quote за 1 KRW)")),
                ("draft_rate", models.DecimalField(blank=True, decimal_places=10, max_digits=18, null=True, verbose_name="Черновик курса")),
                ("draft_source", models.CharField(blank=True, max_length=64, verbose_name="Источник черновика")),
                ("draft_updated_at", models.DateTimeField(blank=True, null=True, verbose_name="Черновик обновлён")),
                ("sort", models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
            ],
            options={
                "verbose_name": "Пара валют",
                "verbose_name_plural": "Пары валют (KRW→)",
                "ordering": ("sort", "quote"),
            },
        ),
        migrations.AddConstraint(
            model_name="currencypair",
            constraint=models.UniqueConstraint(fields=("base", "quote"), name="uniq_currency_pair_base_quote"),
        ),
        migrations.RunPython(seed_pairs, unseed_pairs),
    ]
