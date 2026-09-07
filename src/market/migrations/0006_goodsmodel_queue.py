from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0005_goodsmodel_weight"),
    ]

    operations = [
        migrations.AddField(
            model_name="goodsmodel",
            name="queue",
            field=models.IntegerField(blank=True, null=True, verbose_name="Очередь в списке"),
        ),
    ]
