from datetime import datetime, timedelta

from django import forms

from django.forms import BooleanField, Form, DateField, DateInput, TimeField, TimeInput, IntegerField, NumberInput

from django.core.exceptions import ValidationError
from django.utils import timezone

from booking.models import Table, Feedback
from constants import WORK_SCHEDULE


class StyleFormMixin:
    """Класс для задания стилей формам."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for (
            field_name,
            field,
        ) in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class TableForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Table
        fields = ["number", "photo", "table_type", "description", "is_active", "min_guests", "max_guests"]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["min_guests"] < 1:
            raise ValidationError("Минимальное количество гостей должно быть больше 0.")
        if self.cleaned_data["min_guests"] > self.cleaned_data["max_guests"]:
            raise ValidationError("Минимальное количество гостей не может быть больше максимального.")
        else:
            return self.cleaned_data

    def clean_photo(self):
        """Функция для валидации изображения товара."""
        photo = self.cleaned_data.get("photo")
        max_size = 5 * 1024 * 1024
        if not photo:
            return None
        if photo.size > max_size:
            raise ValidationError("Размер изображения не должен превышать 5 МБ.")
        if not photo.name.endswith((".jpg", ".png")):
            raise ValidationError("Формат файла изображения должен быть .jpg или .png.")
        else:
            return photo


class BookingParametersForm(Form):
    reservation_date = DateField(
        label="Дата",
        widget=DateInput(attrs={"type": "date", "min": timezone.now().date().isoformat(), "class": "form-control"}),
        initial=timezone.now().date().isoformat(),
    )
    start_time = TimeField(label="Время", widget=TimeInput(attrs={"type": "time", "class": "form-control"}))
    guests_count = IntegerField(
        label="Количество гостей",
        min_value=1,
        max_value=10,
        widget=NumberInput(attrs={"class": "form-control", "value": 1}),
    )
    duration = IntegerField(
        label="Длительность (часы)",
        min_value=1,
        max_value=8,
        widget=NumberInput(attrs={"class": "form-control", "value": 2}),
    )

    def clean(self):
        cleaned_data = super().clean()
        reservation_date = cleaned_data.get("reservation_date")
        start_time = cleaned_data.get("start_time")
        duration = cleaned_data.get("duration")

        now = timezone.now()

        if reservation_date < now.date():
            raise ValidationError("Нельзя выбрать прошедшую дату.")
        if reservation_date == now.date():
            if start_time < now.time():
                raise ValidationError("Нельзя выбрать прошедшее время.")
        if reservation_date and start_time and duration:
            day_of_week = reservation_date.weekday()
            work_start, work_end = WORK_SCHEDULE.get(day_of_week, (None, None))
            if work_start is None or work_end is None:
                raise ValidationError("В этот день заведение закрыто.")
            if not (work_start <= start_time < work_end):
                raise ValidationError(f"Ресторан работает с {work_start} до {work_end}.")
            start_min = start_time.hour * 60 + start_time.minute
            end_min = work_end.hour * 60 + work_end.minute
            if start_min + duration * 60 > end_min:
                raise ValidationError(
                    f"Выбранное время ({start_time}) и длительность ({duration} ч.) "
                    f"выходят за рамки рабочего дня (закрытие в {work_end})."
                )

        return cleaned_data


class FeedbackForm(Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    subject = forms.ChoiceField(
        choices=[
            ("booking", "Бронирование столика"),
            ("event", "Организация мероприятия"),
            ("feedback", "Отзыв о ресторане"),
            ("complaint", "Жалоба"),
            ("other", "Другое"),
        ]
    )
    message = forms.CharField(widget=forms.Textarea)


class FeedbackCreateForm(forms.ModelForm):
    """
    Форма отправки обратной связи
    """

    class Meta:
        model = Feedback
        fields = ("subject", "email", "content")

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control", "autocomplete": "off"})
