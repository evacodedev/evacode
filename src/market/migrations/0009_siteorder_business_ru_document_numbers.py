from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0008_siteorder_short_public_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteorder",
            name="business_ru_order_number",
            field=models.CharField(blank=True, max_length=32, verbose_name="№ заказа Business.Ru"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="business_ru_payment_number",
            field=models.CharField(blank=True, max_length=32, verbose_name="№ оплаты Business.Ru"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="business_ru_reservation_number",
            field=models.CharField(blank=True, max_length=32, verbose_name="№ резерва Business.Ru"),
        ),
    ]
