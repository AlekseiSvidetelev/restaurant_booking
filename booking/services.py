from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from booking.models import Reservation
from config.settings import CACHE_ENABLED

from users.models import User


def get_reservation_for_table(table_id):
    """Получение бронирования по id столика"""
    pass


def send_contact_email_message(subject, email, content, ip, user_id):
    """
    Функция отправки сообщения на почту
    """
    user = User.objects.get(id=user_id) if user_id else None
    message = render_to_string(
        "booking/feedback_email_send.html",
        {
            "email": email,
            "content": content,
            "ip": ip,
            "user": user,
        },
    )
    email = EmailMessage(subject, message, settings.SERVER_EMAIL, settings.HELP_EMAIL)
    email.send(fail_silently=False)


def get_client_ip(request):
    """
    Получение IP клиента
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
    return ip
