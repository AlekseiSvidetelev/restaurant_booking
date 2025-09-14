from django.urls import path

from booking.apps import BookingConfig
from booking.views import (
    HomeView,
    # BookingListView,
    TableListView,
    TableCreateView,
    TableDetailView,
    TableUpdateView,
    TableDeleteView,
    AboutView,
    ContactsView,
    TableSelectionView,
    BookingConfirmView,
    BookingStartView,
    BookingListView,
    BookingDetailView,
    BookingDeleteView, FeedbackCreateView,
)

app_name = BookingConfig.name

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("contact/", FeedbackCreateView.as_view(), name="contact"),


    path("table_list/", TableListView.as_view(), name="table_list"),
    path("table_create/", TableCreateView.as_view(), name="table_create"),
    path("table_detail/<int:pk>/", TableDetailView.as_view(), name="table_detail"),
    path("table_update/<int:pk>/", TableUpdateView.as_view(), name="table_update"),
    path("table_delete/<int:pk>/", TableDeleteView.as_view(), name="table_delete"),


    path("booking_list/", BookingListView.as_view(), name="booking_list"),
    path("booking_detail/<int:pk>/", BookingDetailView.as_view(), name="booking_detail"),
    path("booking_delete/<int:pk>/", BookingDeleteView.as_view(), name="booking_delete"),
    path("booking/", BookingStartView.as_view(), name="booking_start"),
    path("booking/tables/", TableSelectionView.as_view(), name="table_selection"),
    path("booking/confirm/<int:table_id>/", BookingConfirmView.as_view(), name="booking_confirm"),
    path('feedback/', FeedbackCreateView.as_view(), name='feedback'),
]
