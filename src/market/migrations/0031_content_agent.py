from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0030_siteorder_confirmation_email_sent_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="productcontent",
            name="agent_draft",
            field=models.JSONField(blank=True, null=True, verbose_name="Черновик агента"),
        ),
        migrations.AddField(
            model_name="productcontent",
            name="agent_error",
            field=models.TextField(blank=True, verbose_name="Ошибка агента"),
        ),
        migrations.AddField(
            model_name="productcontent",
            name="agent_run_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Агент запускался"),
        ),
        migrations.CreateModel(
            name="ProductContentAgentSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "enabled",
                    models.BooleanField(
                        default=False,
                        help_text="Выключен — кнопки и команда не ходят в LLM. Промпт можно править заранее.",
                        verbose_name="Агент включён",
                    ),
                ),
                (
                    "model",
                    models.CharField(
                        default="gpt-4.1-mini",
                        help_text="Имя модели у провайдера, например gpt-4.1-mini",
                        max_length=64,
                        verbose_name="Модель",
                    ),
                ),
                ("prompt", models.TextField(verbose_name="Промпт / правила")),
            ],
            options={
                "verbose_name": "Агент контента",
                "verbose_name_plural": "Агент контента",
            },
        ),
    ]
