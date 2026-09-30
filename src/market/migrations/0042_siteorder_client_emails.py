from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0041_siteorder_status_manager"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteorder",
            name="accepted_email_sent_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Письмо «принят в обработку»"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="tracking_number",
            field=models.CharField(blank=True, max_length=64, verbose_name="Трек-номер EMS"),
        ),
        migrations.AddField(
            model_name="siteorder",
            name="tracking_email_sent_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Письмо с трек-номером"),
        ),
    ]
