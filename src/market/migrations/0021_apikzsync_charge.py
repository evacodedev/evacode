from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0020_apikzsync_posting"),
    ]

    operations = [
        migrations.AddField(
            model_name="apikzsync",
            name="last_charge_id",
            field=models.CharField(blank=True, max_length=32, verbose_name="ID списания BR"),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="last_charge_number",
            field=models.CharField(blank=True, max_length=32, verbose_name="№ списания"),
        ),
    ]
