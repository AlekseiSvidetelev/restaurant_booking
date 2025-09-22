from django.core.management import BaseCommand

from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(email="admin2@example.com", first_name="admin", last_name="admin")
        user.set_password("123456")
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        if created:
            print(f"Создан суперпользователь: {user.email}")
        else:
            print(f"Суперпользователь уже существует: {user.email}")
