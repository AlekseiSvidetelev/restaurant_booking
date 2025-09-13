from time import timezone

from django import forms

from django.forms import BooleanField

from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

from booking.models import Reservation, Table


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
        fields = ["number", "seats", "table_type", "description", "is_active", "min_guests", "max_guests"]


class BookingParametersForm(forms.Form):
    reservation_date = forms.DateField(
        label="Дата",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'min': timezone.now().date().isoformat(),
            'class': 'form-control'
        })
    )
    start_time = forms.TimeField(
        label="Время",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )
    guests_count = forms.IntegerField(
        label="Количество гостей",
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'value': 2
        })
    )
    duration = forms.IntegerField(
        label="Длительность (часы)",
        min_value=1,
        max_value=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'value': 2
        })
    )


