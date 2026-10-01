from django.db import migrations

OLD_TELEGRAM = "https://t.me/+77470483761"
NEW_TELEGRAM = "https://t.me/+77776868917"


def replace_contacts_telegram(apps, schema_editor):
    Contacts = apps.get_model("core", "Contacts")
    Contacts.objects.filter(telegram=OLD_TELEGRAM).update(telegram=NEW_TELEGRAM)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_remove_currencypair_base_rate"),
    ]

    operations = [
        migrations.RunPython(replace_contacts_telegram, migrations.RunPython.noop),
    ]
