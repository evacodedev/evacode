from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0029_set_contents_block"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteorder",
            name="confirmation_email_sent_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Письмо клиенту отправлено",
            ),
        ),
    ]
