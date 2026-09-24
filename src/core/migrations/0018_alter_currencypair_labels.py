# Generated manually for CurrencyPair admin labels

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_currencypair"),
    ]

    operations = [
        migrations.AlterField(
            model_name="currencypair",
            name="rate",
            field=models.DecimalField(
                decimal_places=10,
                help_text="Quote за 1 KRW. Используется на витрине, в калькуляторе и PayPal.",
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
                help_text="Черновик с Frankfurter + ЦБ. На витрину не влияет, пока не принят.",
                max_digits=18,
                null=True,
                verbose_name="API курс",
            ),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="draft_source",
            field=models.CharField(blank=True, max_length=64, verbose_name="Источник API курса"),
        ),
        migrations.AlterField(
            model_name="currencypair",
            name="draft_updated_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="API курс обновлён"),
        ),
    ]
