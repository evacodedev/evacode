from django.db import migrations

NEW_TELEGRAM = "https://t.me/+77470483761"


def update_contacts_telegram(apps, schema_editor):
    Contacts = apps.get_model("core", "Contacts")
    Contacts.objects.update(telegram=NEW_TELEGRAM)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_update_contacts_address"),
    ]

    operations = [
        migrations.RunPython(update_contacts_telegram, migrations.RunPython.noop),
    ]
