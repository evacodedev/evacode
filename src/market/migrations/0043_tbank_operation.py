from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0042_siteorder_client_emails"),
    ]

    operations = [
        migrations.CreateModel(
            name="TBankOperation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operation_id", models.CharField(max_length=80, unique=True, verbose_name="ID операции")),
                (
                    "statement_operation_id",
                    models.CharField(
                        blank=True,
                        help_text="У вебхука и у выписки ID одной операции могут различаться.",
                        max_length=80,
                        verbose_name="ID в выписке",
                    ),
                ),
                ("fingerprint", models.CharField(blank=True, max_length=320, null=True, unique=True)),
                ("account_number", models.CharField(blank=True, db_index=True, max_length=22, verbose_name="Счёт")),
                ("operation_date", models.DateTimeField(blank=True, null=True, verbose_name="Дата операции")),
                ("operation_status", models.CharField(blank=True, max_length=32, verbose_name="Статус операции")),
                ("type_of_operation", models.CharField(blank=True, max_length=16, verbose_name="Тип")),
                ("document_number", models.CharField(blank=True, max_length=32, verbose_name="Номер документа")),
                ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name="Сумма")),
                (
                    "ruble_amount",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name="Сумма, ₽"),
                ),
                ("currency_code", models.CharField(blank=True, max_length=3, verbose_name="Валюта")),
                ("pay_purpose", models.TextField(blank=True, verbose_name="Назначение платежа")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("payer_name", models.CharField(blank=True, max_length=255, verbose_name="Плательщик")),
                ("payer_inn", models.CharField(blank=True, max_length=12, verbose_name="ИНН плательщика")),
                ("payer_account", models.CharField(blank=True, max_length=22, verbose_name="Счёт плательщика")),
                ("receiver_name", models.CharField(blank=True, max_length=255, verbose_name="Получатель")),
                ("receiver_inn", models.CharField(blank=True, max_length=12, verbose_name="ИНН получателя")),
                ("receiver_account", models.CharField(blank=True, max_length=22, verbose_name="Счёт получателя")),
                (
                    "match_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("matched", "Найден"),
                            ("amount_differs", "Сумма не сходится"),
                            ("name_differs", "Имя плательщика другое"),
                            ("by_payer", "По сумме и имени"),
                            ("amount_unknown", "Сумма не посчитана"),
                            ("unmatched", "Не найден"),
                        ],
                        default="",
                        max_length=32,
                        verbose_name="Сверка",
                    ),
                ),
                ("match_note", models.CharField(blank=True, max_length=255, verbose_name="Комментарий сверки")),
                ("source", models.CharField(blank=True, max_length=16, verbose_name="Источник")),
                ("raw", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tbank_operations",
                        to="market.siteorder",
                        verbose_name="Заказ",
                    ),
                ),
            ],
            options={
                "verbose_name": "Операция Т-Банка",
                "verbose_name_plural": "Операции Т-Банка",
                "ordering": ["-operation_date", "-id"],
            },
        ),
    ]
