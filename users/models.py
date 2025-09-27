from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    username = None
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150,
    )
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
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.email


class Employee(models.Model):

    POSTS = (
        ("Senior Administrator", "Старший администратор"),
        ("Administrator", "Администратор"),
        ("Waiter", "Официант"),
        ("Bartender", "Бармен"),
        ("Sommelier", "Сомелье"),
        ("Chef", "Шеф-повар"),
        ("Cook", "Повар"),
    )
    EMPLOYEE_STATUSES = (
        ("working", "Работает"),
        ("fired", "Уволен"),
        ("probationary_period", "Испытательный срок"),
        ("training", "Отпуск"),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee",
        verbose_name="Пользователь",
    )
    birthday = models.DateField(
        verbose_name="Дата рождения",
        blank=True,
        null=True,
        help_text="Введите дату рождения",
    )
    post = models.CharField(
        choices=POSTS,
        verbose_name="Должность",
        help_text="Выберите должность",
        max_length=150,
    )
    photo = models.ImageField(
        upload_to="employee/avatars",
        blank=True,
        null=True,
        verbose_name="Фото",
    )
    personal_data = models.TextField(
        verbose_name="Личные данные",
        blank=True,
        null=True,
        help_text="Введите личные данные",
    )
    date_employment = models.DateField(
        verbose_name="Дата приема на работу",
        blank=True,
        null=True,
        help_text="Введите дату приема на работу",
    )
    status = models.CharField(
        max_length=150,
        choices=EMPLOYEE_STATUSES,
        default="working",
        verbose_name="Статус",
        help_text="Выберите статус",
    )

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        permissions = [
            ("can_view_all_employees", "Может просматривать всех сотрудников"),
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
