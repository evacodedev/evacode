from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0031_content_agent"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteorder",
            name="paypal_mode",
            field=models.CharField(
                blank=True,
                help_text="live или sandbox. Нужен, чтобы capture шёл в тот же контур, где создали заказ.",
                max_length=16,
                verbose_name="Режим PayPal",
            ),
        ),
    ]
