from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0006_siteorder_payment_receipt"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteorder",
            name="business_ru_reservation_id",
            field=models.CharField(blank=True, max_length=32, verbose_name="ID резерва Business.Ru"),
        ),
    ]
