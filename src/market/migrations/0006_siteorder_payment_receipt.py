from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0005_siteorder"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteorder",
            name="paypal_receipt_url",
            field=models.TextField(blank=True, verbose_name="Ссылка на чек PayPal"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="business_ru_payment_id",
            field=models.CharField(blank=True, max_length=32, verbose_name="ID оплаты Business.Ru"),
        ),
    ]
