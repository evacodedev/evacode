from django.db import migrations, models


def create_defaults(apps, schema_editor):
    CheckoutSettings = apps.get_model("market", "CheckoutSettings")
    CheckoutSettings.objects.get_or_create(
        pk=1,
        defaults={"paypal_enabled": False, "telegram_enabled": False},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0016_partnerapikey"),
    ]

    operations = [
        migrations.CreateModel(
            name="CheckoutSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("paypal_enabled", models.BooleanField(default=False, verbose_name="PayPal на сайте")),
                ("telegram_enabled", models.BooleanField(default=False, verbose_name="Заказ в Telegram")),
            ],
            options={
                "verbose_name": "Оплата на сайте",
                "verbose_name_plural": "Оплата на сайте",
            },
        ),
        migrations.RunPython(create_defaults, migrations.RunPython.noop),
    ]
