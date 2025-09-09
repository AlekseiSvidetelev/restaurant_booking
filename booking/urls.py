from django.urls import path

from booking.apps import BookingConfig
from booking.views import HomeView, BookingListView, BookingCreateView

app_name = BookingConfig.name

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("list/", BookingListView.as_view(), name="booking_list"),
    path("create/", BookingCreateView.as_view(), name="booking_create"),
]
