from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    username = None
    first_name = models.CharField(verbose_name="Имя пользователя", max_length=150, blank=True, null=True)
    last_name = models.CharField(verbose_name="Фамилия пользователя", max_length=150, blank=True, null=True)
    email = models.EmailField(verbose_name="Email", max_length=255, unique=True)
    phone = models.CharField(
        max_length=35,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Введите ваш номер телефона",
    )
    tg_name = models.CharField(verbose_name="Ник в телеграм", max_length=100, blank=True, null=True)
    avatar = models.ImageField(
        verbose_name="Аватар",
        upload_to="users/avatars",
        blank=True,
        null=True,
        help_text="Загрузите ваш аватар",
    )

    token = models.CharField(verbose_name="Токен", max_length=255, blank=True, null=True)

    reset_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Токен сброса пароля")
    reset_token_created = models.DateTimeField(blank=True, null=True, verbose_name="Время создания токена сброса")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        permissions = [
            ("can_view_all_users", "Можно просматривать всех пользователей"),
        ]

    def __str__(self):
        return self.email
