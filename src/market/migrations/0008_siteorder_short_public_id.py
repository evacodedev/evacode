from django.db import migrations, models
import market.models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0007_siteorder_business_ru_reservation_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siteorder",
            name="public_id",
            field=models.CharField(
                default=market.models.generate_public_id,
                editable=False,
                max_length=36,
                unique=True,
            ),
        ),
    ]
