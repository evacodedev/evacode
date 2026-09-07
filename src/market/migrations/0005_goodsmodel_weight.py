from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0004_groupofgoods_site_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="goodsmodel",
            name="weight",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Вес, г"),
        ),
    ]
