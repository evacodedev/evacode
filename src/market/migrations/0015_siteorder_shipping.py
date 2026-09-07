from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0014_alter_siteorder_business_ru_order_number_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteorder",
            name="goods_krw",
            field=models.PositiveIntegerField(default=0, verbose_name="Товары, ₩"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="shipping_destination",
            field=models.CharField(blank=True, max_length=16, verbose_name="Направление EMS"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="shipping_krw",
            field=models.PositiveIntegerField(default=0, verbose_name="Доставка, ₩"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="shipping_method",
            field=models.CharField(blank=True, max_length=16, verbose_name="Способ доставки"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="weight_grams",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Вес заказа, г"),
        ),
    ]
