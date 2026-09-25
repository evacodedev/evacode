# Generated manually: drop base_rate — исконный = draft_rate (API)

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_currencypair_base_rate"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="currencypair",
            name="base_rate",
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="draft_rate",
            field=models.DecimalField(
                blank=True,
                decimal_places=10,
                help_text="Курс с Frankfurter + ЦБ. Подтягивается кнопкой в админке.",
                max_digits=18,
                null=True,
                verbose_name="Исконный курс (API)",
            ),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="draft_source",
            field=models.CharField(blank=True, max_length=64, verbose_name="Источник API"),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="draft_updated_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="API обновлён"),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="markup",
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal("1.0000"),
                help_text="Только в админке: коммерческий = исконный API × коэффициент. На витрину не уходит.",
                max_digits=8,
                verbose_name="Коэффициент",
            ),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="rate",
            field=models.DecimalField(
                decimal_places=10,
                help_text="Исконный API × коэффициент. Используется на витрине, в калькуляторе и PayPal.",
                max_digits=18,
                verbose_name="Коммерческий курс",
            ),
        ),
    ]
