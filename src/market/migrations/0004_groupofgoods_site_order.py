from django.db import migrations, models


def copy_default_order_to_site_order(apps, schema_editor):
    GroupOfGoods = apps.get_model("market", "GroupOfGoods")
    for group in GroupOfGoods.objects.all().iterator():
        raw = (group.default_order or "").strip()
        if raw.lstrip("-").isdigit():
            group.site_order = int(raw)
            group.save(update_fields=["site_order"])


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0003_groupofgoods_isaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="groupofgoods",
            name="site_order",
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name="Порядок на сайте",
            ),
        ),
        migrations.RunPython(copy_default_order_to_site_order, migrations.RunPython.noop),
    ]
