from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0002_goodsmodel_bestseller"),
    ]

    operations = [
        migrations.AddField(
            model_name="groupofgoods",
            name="isaction",
            field=models.BooleanField(default=True, verbose_name="Показывать на сайте"),
        ),
    ]
