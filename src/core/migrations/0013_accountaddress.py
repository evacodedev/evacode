from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_accountprofile"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountAddress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("city", models.CharField(max_length=128, verbose_name="Город")),
                ("street", models.CharField(max_length=255, verbose_name="Улица")),
                ("house", models.CharField(max_length=32, verbose_name="Дом")),
                ("apartment", models.CharField(blank=True, max_length=32, verbose_name="Квартира")),
                ("comment", models.CharField(blank=True, max_length=255, verbose_name="Комментарий")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account_addresses",
                        to="auth.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Адрес доставки",
                "verbose_name_plural": "Адреса доставки",
                "ordering": ["id"],
            },
        ),
    ]
