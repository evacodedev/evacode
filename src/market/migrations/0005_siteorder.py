import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0004_groupofgoods_site_order"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Ожидает оплату"),
                            ("paid", "Оплачен"),
                            ("failed", "Ошибка оплаты"),
                            ("cancelled", "Отменён"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("first_name", models.CharField(max_length=128, verbose_name="ФИО")),
                ("phone", models.CharField(max_length=64, verbose_name="Телефон")),
                ("phone_digits", models.CharField(blank=True, max_length=32, verbose_name="Телефон (цифры)")),
                ("email", models.EmailField(max_length=254, verbose_name="Email")),
                ("country", models.CharField(max_length=64, verbose_name="Страна")),
                ("city", models.CharField(max_length=128, verbose_name="Город")),
                ("address", models.CharField(max_length=255, verbose_name="Адрес")),
                ("postal_code", models.CharField(blank=True, max_length=32, verbose_name="Индекс")),
                ("comment", models.TextField(blank=True, verbose_name="Комментарий")),
                ("amount_krw", models.PositiveIntegerField(verbose_name="Сумма, ₩")),
                ("amount_usd", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Сумма, USD")),
                (
                    "usd_rate_snapshot",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=16,
                        null=True,
                        verbose_name="Курс KRW→USD",
                    ),
                ),
                ("paypal_order_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("paypal_capture_id", models.CharField(blank=True, max_length=64)),
                ("paypal_payload", models.TextField(blank=True)),
                ("business_ru_partner_id", models.CharField(blank=True, max_length=32)),
                ("business_ru_order_id", models.CharField(blank=True, max_length=32)),
                ("business_ru_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Заказ с сайта",
                "verbose_name_plural": "Заказы с сайта",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SiteOrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("good_id_snapshot", models.PositiveIntegerField(verbose_name="ID товара")),
                ("title", models.CharField(max_length=256, verbose_name="Название")),
                ("quantity", models.PositiveIntegerField(verbose_name="Количество")),
                ("price_krw", models.PositiveIntegerField(verbose_name="Цена, ₩")),
                ("line_total_krw", models.PositiveIntegerField(verbose_name="Сумма, ₩")),
                (
                    "good",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="market.goodsmodel",
                        verbose_name="Товар",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="market.siteorder",
                    ),
                ),
            ],
            options={
                "verbose_name": "Позиция заказа",
                "verbose_name_plural": "Позиции заказа",
            },
        ),
    ]
