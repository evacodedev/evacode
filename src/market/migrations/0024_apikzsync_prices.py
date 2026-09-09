from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0023_apikzsync_pk_sequence"),
    ]

    operations = [
        migrations.AddField(
            model_name="apikzsync",
            name="prices_updated",
            field=models.PositiveIntegerField(default=0, verbose_name="Цен обновлено"),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="prices_unchanged",
            field=models.PositiveIntegerField(default=0, verbose_name="Цен без изменений"),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="prices_failed",
            field=models.PositiveIntegerField(default=0, verbose_name="Цен с ошибкой"),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="prices_goods",
            field=models.PositiveIntegerField(default=0, verbose_name="Товаров с ценами"),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="prices_list_id",
            field=models.CharField(blank=True, max_length=32, verbose_name="ID назначения цен BR"),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="prices_list_number",
            field=models.CharField(blank=True, max_length=32, verbose_name="№ назначения цен"),
        ),
    ]
