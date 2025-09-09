from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView

from booking.forms import ReservationForm
from booking.models import Reservation


class HomeView(TemplateView):
    """Главная страница"""

    template_name = "booking/home.html"


class BookingListView(ListView):

    model = Reservation
    template_name = "booking/booking_list.html"
    context_object_name = "reservations"
    ordering = ["-date"]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Reservation.objects.filter(user=self.request.user)
        else:
            return Reservation.objects.none()


class BookingCreateView(CreateView):

    model = Reservation
    form_class = ReservationForm
    template_name = "booking/booking_form.html"
    success_url = reverse_lazy("booking:booking_list")
