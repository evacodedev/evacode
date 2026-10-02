from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0044_consultant_orders'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteorder',
            name='sent_to_client_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Консультант отправил клиенту на оплату'),
        ),
    ]
