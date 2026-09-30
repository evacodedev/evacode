from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0040_apirusync_prices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siteorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Ожидает оплату"),
                    ("paid", "Оплачен"),
                    ("manager", "Передан консультанту"),
                    ("failed", "Ошибка оплаты"),
                    ("cancelled", "Отменён"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
    ]
