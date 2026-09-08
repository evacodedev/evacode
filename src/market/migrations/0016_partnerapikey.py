from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0015_siteorder_shipping"),
    ]

    operations = [
        migrations.CreateModel(
            name="PartnerApiKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, verbose_name="Партнёр")),
                (
                    "token",
                    models.CharField(
                        blank=True,
                        help_text="Если оставить пустым, сгенерируется при сохранении",
                        max_length=64,
                        unique=True,
                        verbose_name="Токен",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Включён")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
            ],
            options={
                "verbose_name": "Токен API партнёра",
                "verbose_name_plural": "Токены API партнёров",
                "ordering": ["name"],
            },
        ),
    ]
