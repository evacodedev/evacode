from django.db import migrations, models


def refresh_jogabi(apps, schema_editor):
    from market.brand_pages import ensure_jogabi_brand

    ensure_jogabi_brand(link_goods=True)


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0035_productbrand_partnership"),
    ]

    operations = [
        migrations.AddField(
            model_name="productbrand",
            name="video_url",
            field=models.URLField(blank=True, verbose_name="Видео"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="video_title",
            field=models.CharField(blank=True, max_length=256, verbose_name="Заголовок видео"),
        ),
        migrations.RunPython(refresh_jogabi, noop),
    ]
