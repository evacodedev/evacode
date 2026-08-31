from django.db import migrations, models

NEW_ADDRESS = (
    "경기 안산시 단원구 별망로 555 4 этаж №420"
    "<br>"
    "Gyeonggi-do, Ansan-si, Danwon-gu, Byeolmang-ro 555, 4th Floor, No. 420"
)


def update_contacts_address(apps, schema_editor):
    Contacts = apps.get_model("core", "Contacts")
    Contacts.objects.update(address=NEW_ADDRESS)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contacts",
            name="address",
            field=models.CharField(max_length=256, verbose_name="Address"),
        ),
        migrations.RunPython(update_contacts_address, migrations.RunPython.noop),
    ]
