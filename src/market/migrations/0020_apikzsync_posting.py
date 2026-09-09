from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0019_apikzsync"),
    ]

    operations = [
        migrations.AddField(
            model_name="apikzsync",
            name="last_posting_id",
            field=models.CharField(blank=True, max_length=32, verbose_name="ID оприходования BR"),
        ),
        migrations.AddField(
            model_name="apikzsync",
            name="last_posting_number",
            field=models.CharField(blank=True, max_length=32, verbose_name="№ оприходования"),
        ),
    ]
