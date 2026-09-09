from django.db import migrations, models


def create_defaults(apps, schema_editor):
    ApiKzSync = apps.get_model("market", "ApiKzSync")
    ApiKzSync.objects.get_or_create(pk=1)


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0018_alter_checkoutsettings_paypal_enabled_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiKzSync",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_run_at", models.DateTimeField(blank=True, null=True, verbose_name="Последний запуск")),
                ("last_ok", models.BooleanField(default=False, verbose_name="Успешно")),
                ("last_message", models.TextField(blank=True, verbose_name="Результат")),
                (
                    "last_inventory_id",
                    models.CharField(blank=True, max_length=32, verbose_name="ID инвентаризации BR"),
                ),
                (
                    "last_inventory_number",
                    models.CharField(blank=True, max_length=32, verbose_name="№ инвентаризации"),
                ),
            ],
            options={
                "verbose_name": "Синхронизация остатков",
                "verbose_name_plural": "Синхронизация остатков",
            },
        ),
        migrations.RunPython(create_defaults, migrations.RunPython.noop),
    ]
