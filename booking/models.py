from django.db import models

from users.models import User



class Table(models.Model):
    TABLE_TYPES = (
        ("standard", "Стандартный"),
        ("booth", "Бутылочный"),
        ("bar", "Барная стойка"),
        ("vip", "VIP"),
        ("outdoor", "Уличный"),
    )
    number = models.IntegerField(unique=True, verbose_name="Номер стола", help_text="Введите номер стола")

    table_type = models.CharField(max_length=20, choices=TABLE_TYPES, default="standard", verbose_name="Тип столика")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание стола",
        help_text="Введите описание стола",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен", help_text="Активен ли стол?")
    min_guests = models.PositiveIntegerField(
        default=1,
        verbose_name="Минимальное количество гостей",
        help_text="Введите минимальное количество гостей",
    )
    max_guests = models.PositiveIntegerField(
        verbose_name="Максимальное количество гостей",
        help_text="Введите максимальное количество гостей",
    )
    photo = models.ImageField(
        verbose_name="Превью",
        upload_to="tables/previews",
        blank=True,
        null=True,
        help_text="Загрузите превью стола",
    )

    def __str__(self):
        return f"Стол {self.number} - от {self.min_guests} до {self.max_guests} мест"

    class Meta:
        verbose_name = "Стол"
        verbose_name_plural = "Столы"
        ordering = ["number"]
        permissions = [
            ("administrate_tables", "Может добавлять и редактировать столы"),
            ("super_administrate_tables", "Может добавлять, редактировать, удалять столы"),
        ]


class Reservation(models.Model):
    STATUS_CHOICES = (
        ("confirmed", "Подтверждено"),
        ("canceled", "Отменено"),
        ("completed", "Завершено"),
        ("no_show", "Не явился"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", help_text="Пользователь")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Столик", help_text="Столик")
    guests_count = models.PositiveSmallIntegerField(
        verbose_name="Количество гостей",
        help_text="Количество гостей",
    )
    reservation_date = models.DateField(
        verbose_name="Дата бронирования",
        help_text="Дата бронирования",
    )
    start_time = models.TimeField(
        verbose_name="Время начала",
        help_text="Время начала",
    )
    end_time = models.TimeField(
        verbose_name="Время окончания",
        help_text="Время окончания",
    )
    duration = models.PositiveIntegerField(
        verbose_name="Длительность час",
        help_text="Длительность бронирования в часах",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="confirmed",
        verbose_name="Статус",
        help_text="Статус бронирования",
    )
    special_requests = models.TextField(
        blank=True,
        verbose_name="Особые пожелания",
        help_text="Особые пожелания",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
        help_text="Дата обновления",
    )

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ["-reservation_date", "start_time"]
        permissions = [
            ("can_cancel_reservation", "Может отменять бронирование"),
            ("can_update_status_reservation", "Может менять статус бронирования"),
            ("can_delete_reservation", "Может удалять бронирование"),
        ]

    def __str__(self):
        return f"Бронирование #{self.id} - {self.reservation_date} {self.start_time}"


class Feedback(models.Model):
    """
    Модель обратной связи
    """
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    email = models.EmailField(max_length=255, verbose_name='Электронный адрес (email)')
    content = models.TextField(verbose_name='Содержимое письма')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    ip_address = models.GenericIPAddressField(verbose_name='IP отправителя',  blank=True, null=True)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        ordering = ['-time_create']
        db_table = 'app_feedback'

    def __str__(self):
        return f'Вам письмо от {self.email}'
