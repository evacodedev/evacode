from datetime import time as dt_time

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0025_apikzsyncsettings"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="apikzsyncsettings",
            name="interval_hours",
        ),
        migrations.AddField(
            model_name="apikzsyncsettings",
            name="weekdays",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Можно выбрать несколько дней. Время одно на все выбранные дни.",
                max_length=32,
                verbose_name="Дни недели",
            ),
        ),
        migrations.AddField(
            model_name="apikzsyncsettings",
            name="run_time",
            field=models.TimeField(
                default=dt_time(3, 0),
                help_text="Часы и минуты в поясе сервера — смотрите часы на этой странице.",
                verbose_name="Время запуска",
            ),
        ),
    ]
