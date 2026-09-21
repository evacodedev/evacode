from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_update_contacts_telegram"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(blank=True, max_length=64, verbose_name="Телефон")),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="Дата рождения")),
                ("whatsapp", models.CharField(blank=True, max_length=64, verbose_name="WhatsApp")),
                ("telegram", models.CharField(blank=True, max_length=64, verbose_name="Telegram")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account_profile",
                        to="auth.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Профиль покупателя",
                "verbose_name_plural": "Профили покупателей",
            },
        ),
    ]
