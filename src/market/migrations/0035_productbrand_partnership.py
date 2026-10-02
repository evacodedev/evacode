from django.db import migrations, models


def refresh_jogabi(apps, schema_editor):
    # Живая модель ProductBrand уже с video_url (0036); заполнение повторяет 0036.
    return None


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0034_productbrand_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="productbrandi18n",
            name="history_title",
            field=models.CharField(blank=True, max_length=256, verbose_name="Заголовок истории"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="mission_title",
            field=models.CharField(blank=True, max_length=256, verbose_name="Заголовок миссии"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="partnership_title",
            field=models.CharField(blank=True, max_length=256, verbose_name="Заголовок партнёрства"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="partnership",
            field=models.TextField(blank=True, verbose_name="Партнёрство"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="gallery",
            field=models.JSONField(blank=True, default=list, verbose_name="Галерея"),
        ),
        migrations.RunPython(refresh_jogabi, noop),
    ]
