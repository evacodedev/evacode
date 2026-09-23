from django.db import migrations


def seed_curacion(apps, schema_editor):
    from market.brand_pages import ensure_curacion_brand

    ensure_curacion_brand(link_goods=True)


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0036_productbrand_video"),
    ]

    operations = [
        migrations.RunPython(seed_curacion, noop),
    ]
