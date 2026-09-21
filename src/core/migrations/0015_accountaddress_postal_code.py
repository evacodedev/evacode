from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_accountaddress_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="accountaddress",
            name="postal_code",
            field=models.CharField(default="", max_length=32, verbose_name="Индекс"),
            preserve_default=False,
        ),
    ]
