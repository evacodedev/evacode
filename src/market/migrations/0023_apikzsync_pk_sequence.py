from django.db import migrations


def reset_apikzsync_sequence(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT setval(
                pg_get_serial_sequence('market_apikzsync', 'id'),
                COALESCE((SELECT MAX(id) FROM market_apikzsync), 1)
            )
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0022_apikzsync_history"),
    ]

    operations = [
        migrations.RunPython(reset_apikzsync_sequence, migrations.RunPython.noop),
    ]
