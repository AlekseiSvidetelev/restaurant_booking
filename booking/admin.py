from django.contrib import admin

from booking.models import Feedback, Table, Reservation


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):

    list_display = ("id", "number", "is_active", "min_guests", "max_guests")
    search_fields = ("number",)


@admin.register(Reservation)
class BookingAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "table", "guests_count", "reservation_date", "start_time", "duration")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):

    list_display = ("email", "ip_address", "user")
    list_display_links = ("email", "ip_address")
