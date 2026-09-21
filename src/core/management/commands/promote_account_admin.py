from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Grant Django admin (staff + superuser) to an account by email."

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, **options):
        email = (options["email"] or "").strip().lower()
        if not email:
            raise CommandError("Укажите email")
        user = (
            User.objects.filter(username__iexact=email).first()
            or User.objects.filter(email__iexact=email).first()
        )
        if not user:
            raise CommandError(f"Пользователь {email} не найден")
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if not (user.email or "").strip():
            user.email = email
        user.save(update_fields=["is_staff", "is_superuser", "is_active", "email"])
        self.stdout.write(self.style.SUCCESS(f"Админ: {user.username} id={user.pk}"))
