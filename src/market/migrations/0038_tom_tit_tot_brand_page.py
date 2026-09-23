from django.db import migrations


def seed_tom_tit_tot(apps, schema_editor):
    from market.brand_pages import ensure_tom_tit_tot_brand

    ensure_tom_tit_tot_brand(link_goods=True)


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0037_curacion_brand_page"),
    ]

    operations = [
        migrations.RunPython(seed_tom_tit_tot, noop),
    ]
