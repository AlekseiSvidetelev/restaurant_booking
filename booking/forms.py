from django import forms
from django.forms import BooleanField

from booking.models import Reservation


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


class ReservationForm(StyleFormMixin, forms.ModelForm):

    class Meta:
        model = Reservation
        fields = ["reservation_date", "guests_count", "duration"]
