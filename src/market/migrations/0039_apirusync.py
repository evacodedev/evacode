from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0038_tom_tit_tot_brand_page"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiRuSync",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("store_id", models.CharField(blank=True, db_index=True, max_length=32, verbose_name="ID склада BR")),
                ("run_at", models.DateTimeField(auto_now_add=True, verbose_name="Запуск")),
                ("ok", models.BooleanField(default=False, verbose_name="Успешно")),
                ("message", models.TextField(blank=True, verbose_name="Результат")),
                ("inventory_id", models.CharField(blank=True, max_length=32, verbose_name="ID инвентаризации BR")),
                ("inventory_number", models.CharField(blank=True, max_length=32, verbose_name="№ инвентаризации")),
                ("posting_id", models.CharField(blank=True, max_length=32, verbose_name="ID оприходования BR")),
                ("posting_number", models.CharField(blank=True, max_length=32, verbose_name="№ оприходования")),
                ("charge_id", models.CharField(blank=True, max_length=32, verbose_name="ID списания BR")),
                ("charge_number", models.CharField(blank=True, max_length=32, verbose_name="№ списания")),
            ],
            options={
                "verbose_name": "Запуск синхронизации RU",
                "verbose_name_plural": "История синхронизаций RU",
                "ordering": ("-run_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="ApiRuSyncSettings",
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
                    "weekdays",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Можно выбрать несколько дней. Время одно на все выбранные дни.",
                        max_length=32,
                        verbose_name="Дни недели",
                    ),
                ),
                (
                    "run_time",
                    models.TimeField(
                        default=datetime.time(3, 0),
                        help_text="Часы и минуты в поясе сервера — смотрите часы на этой странице.",
                        verbose_name="Время запуска",
                    ),
                ),
            ],
            options={
                "verbose_name": "Расписание синхронизации RU",
                "verbose_name_plural": "Расписание синхронизации RU",
            },
        ),
    ]
