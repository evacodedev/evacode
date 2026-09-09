from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def create_defaults(apps, schema_editor):
    ApiKzSyncSettings = apps.get_model("market", "ApiKzSyncSettings")
    ApiKzSyncSettings.objects.get_or_create(
        pk=1,
        defaults={"enabled": False, "interval_hours": 24},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0024_apikzsync_prices"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiKzSyncSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "enabled",
                    models.BooleanField(
                        default=False,
                        help_text="Пока выключено, фоновый воркер не запускает синхронизацию. Ручной запуск из истории работает всегда.",
                        verbose_name="Расписание включено",
                    ),
                ),
                (
                    "interval_hours",
                    models.PositiveIntegerField(
                        default=24,
                        help_text="Отсчёт от последнего запуска (по расписанию или вручную). От 1 до 168 часов.",
                        validators=[MinValueValidator(1), MaxValueValidator(168)],
                        verbose_name="Интервал, часов",
                    ),
                ),
            ],
            options={
                "verbose_name": "Расписание синхронизации",
                "verbose_name_plural": "Расписание синхронизации",
            },
        ),
        migrations.RunPython(create_defaults, migrations.RunPython.noop),
    ]
