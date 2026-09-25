# Generated manually: CurrencyPair.markup

from decimal import Decimal

from django.db import migrations, models


DEFAULT_MARKUPS = {
    "USD": Decimal("1.0700"),
    "EUR": Decimal("1.0700"),
    "RUB": Decimal("1.0550"),
    "KZT": Decimal("1.0550"),
    "KGS": Decimal("1.0550"),
    "UZS": Decimal("1.0550"),
}


def set_default_markups(apps, schema_editor):
    CurrencyPair = apps.get_model("core", "CurrencyPair")
    for quote, markup in DEFAULT_MARKUPS.items():
        CurrencyPair.objects.filter(base="KRW", quote=quote).update(markup=markup)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_alter_currencypair_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="currencypair",
            name="markup",
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal("1.0000"),
                help_text="Множитель к цене после курса. Например 1.0700 = +7%, 1.0550 = +5,5%.",
                max_digits=8,
                verbose_name="Коэффициент наценки",
            ),
        ),
        migrations.RunPython(set_default_markups, noop_reverse),
    ]
