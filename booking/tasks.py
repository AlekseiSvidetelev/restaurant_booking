from celery import shared_task
from django.utils import timezone
from .models import Reservation


@shared_task
def auto_complete_expired_bookings():
    now = timezone.now()
    expired_bookings = Reservation.objects.filter(status="confirmed", end_time__lte=now)
    updated_count = expired_bookings.update(status="completed")

    return f"Завершено {updated_count} просроченных бронирований."
