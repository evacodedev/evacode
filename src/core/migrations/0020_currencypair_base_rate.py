# Generated manually: CurrencyPair.base_rate + commercial = base × markup

from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models

RATE_QUANT = Decimal("0.0000000001")


def fill_base_and_commercial(apps, schema_editor):
    CurrencyPair = apps.get_model("core", "CurrencyPair")
    for pair in CurrencyPair.objects.all():
        base = Decimal(str(pair.rate))
        markup = Decimal(str(pair.markup or "1"))
        if markup <= 0:
            markup = Decimal("1")
        commercial = (base * markup).quantize(RATE_QUANT, rounding=ROUND_HALF_UP)
        CurrencyPair.objects.filter(pk=pair.pk).update(base_rate=base, rate=commercial)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_currencypair_markup"),
    ]

    operations = [
        migrations.AddField(
            model_name="currencypair",
            name="base_rate",
            field=models.DecimalField(
                decimal_places=10,
                help_text="Базовый курс (ручной или принятый с API). Не используется в операциях напрямую.",
                max_digits=18,
                null=True,
                verbose_name="Исконный курс",
            ),
        ),
        migrations.RunPython(fill_base_and_commercial, noop_reverse),
        migrations.AlterField(
            model_name="currencypair",
            name="base_rate",
            field=models.DecimalField(
                decimal_places=10,
                help_text="Базовый курс (ручной или принятый с API). Не используется в операциях напрямую.",
                max_digits=18,
                verbose_name="Исконный курс",
            ),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="markup",
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal("1.0000"),
                help_text="Только для расчёта коммерческого курса в админке. Например 1.0700 = +7%.",
                max_digits=8,
                verbose_name="Коэффициент наценки",
            ),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="rate",
            field=models.DecimalField(
                decimal_places=10,
                help_text="Исконный × коэффициент. Используется на витрине, в калькуляторе и PayPal.",
                max_digits=18,
                verbose_name="Коммерческий курс",
            ),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="draft_rate",
            field=models.DecimalField(
                blank=True,
                decimal_places=10,
                help_text="Черновик с Frankfurter + ЦБ. При принятии пишется в исконный, коммерческий пересчитывается.",
                max_digits=18,
                null=True,
                verbose_name="API курс",
            ),
        ),
    ]
