from django import forms

from django.forms import BooleanField, Form, DateField, DateInput, TimeField, TimeInput, IntegerField, NumberInput

from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from booking.models import Reservation, Table, Feedback
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
        fields = ["number", "photo","table_type", "description", "is_active", "min_guests", "max_guests"]


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

        if not (reservation_date and start_time and duration):
            return cleaned_data

        tz = timezone.get_default_timezone()
        now_in_tz = timezone.now().astimezone(tz)

        if reservation_date < now_in_tz.date() and start_time < now_in_tz.time():
            raise ValidationError("Нельзя выбрать прошедшее время.")

        full_start_time = datetime.combine(reservation_date, start_time)
        day_of_week = reservation_date.weekday()
        work_start, work_end = WORK_SCHEDULE.get(day_of_week, (None, None))

        if work_start is None or work_end is None:
            raise ValidationError("В этот день заведение закрыто.")

        closing_time = datetime.combine(reservation_date, work_end)
        required_duration = timedelta(hours=duration)

        if closing_time - full_start_time < required_duration:
            raise ValidationError(
                f"Выбранное время недостаточно для бронирования длительностью {duration} ч. "
                f"Закрытие заведения в {work_end}."
            )

        return cleaned_data

class FeedbackForm(Form):

    name    = forms.CharField(max_length=100)
    email   = forms.EmailField()
    phone   = forms.CharField(max_length=20, required=False)
    subject = forms.ChoiceField(choices=[
        ('booking','Бронирование столика'),
        ('event','Организация мероприятия'),
        ('feedback','Отзыв о ресторане'),
        ('complaint','Жалоба'),
        ('other','Другое'),
    ])
    message = forms.CharField(widget=forms.Textarea)


class FeedbackCreateForm(forms.ModelForm):
    """
    Форма отправки обратной связи
    """

    class Meta:
        model = Feedback
        fields = ('subject', 'email', 'content')

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
