from django.db import migrations, models
from django.utils import timezone


def cleanup_empty_singleton(apps, schema_editor):
    ApiKzSync = apps.get_model("market", "ApiKzSync")
    ApiKzSync.objects.filter(run_at__isnull=True, message="").delete()
    ApiKzSync.objects.filter(run_at__isnull=True).update(run_at=timezone.now())
    ApiKzSync.objects.filter(warehouse_code="").update(warehouse_code="KZ")
    ApiKzSync.objects.filter(store_id="").update(store_id="2787290")


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0021_apikzsync_charge"),
    ]

    operations = [
        migrations.RenameField(model_name="apikzsync", old_name="last_run_at", new_name="run_at"),
        migrations.RenameField(model_name="apikzsync", old_name="last_ok", new_name="ok"),
        migrations.RenameField(model_name="apikzsync", old_name="last_message", new_name="message"),
        migrations.RenameField(model_name="apikzsync", old_name="last_inventory_id", new_name="inventory_id"),
        migrations.RenameField(
            model_name="apikzsync",
            old_name="last_inventory_number",
            new_name="inventory_number",
        ),
        migrations.RenameField(model_name="apikzsync", old_name="last_posting_id", new_name="posting_id"),
        migrations.RenameField(
            model_name="apikzsync",
            old_name="last_posting_number",
            new_name="posting_number",
        ),
        migrations.RenameField(model_name="apikzsync", old_name="last_charge_id", new_name="charge_id"),
        migrations.RenameField(
            model_name="apikzsync",
            old_name="last_charge_number",
            new_name="charge_number",
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="warehouse_code",
            field=models.CharField(
                choices=[("KZ", "Казахстан"), ("RU", "Россия"), ("UZ", "Узбекистан")],
                db_index=True,
                default="KZ",
                max_length=8,
                verbose_name="Склад",
            ),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="store_id",
            field=models.CharField(blank=True, db_index=True, max_length=32, verbose_name="ID склада BR"),
        ),
        migrations.RunPython(cleanup_empty_singleton, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="apikzsync",
            name="run_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Запуск"),
        ),
        migrations.AlterModelOptions(
            name="apikzsync",
            options={
                "ordering": ("-run_at", "-id"),
                "verbose_name": "Запуск синхронизации",
                "verbose_name_plural": "История синхронизаций",
            },
        ),
    ]
