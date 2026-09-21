from django.db import migrations


ADMIN_EMAIL = "vadim.k@evacode.co.kr"


def promote_tester(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(username__iexact=ADMIN_EMAIL).update(
        is_staff=True,
        is_superuser=True,
        is_active=True,
        email=ADMIN_EMAIL,
    )
    User.objects.filter(email__iexact=ADMIN_EMAIL).update(
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_accountaddress_postal_code"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(promote_tester, noop),
    ]
