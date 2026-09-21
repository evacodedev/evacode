from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_accountaddress"),
    ]

    operations = [
        migrations.AddField(
            model_name="accountaddress",
            name="country",
            field=models.CharField(blank=True, max_length=64, verbose_name="Страна"),
        ),
        migrations.AddField(
            model_name="accountaddress",
            name="country_code",
            field=models.CharField(blank=True, max_length=8, verbose_name="Код страны"),
        ),
    ]
