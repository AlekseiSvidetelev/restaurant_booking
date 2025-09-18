from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    TemplateView,
    ListView,
    CreateView,
    UpdateView,
    DetailView,
    DeleteView,
    FormView,
    RedirectView,
)
from booking.forms import TableForm, BookingParametersForm, FeedbackCreateForm
from booking.models import Reservation, Table, Feedback
from django.utils import timezone
from datetime import datetime, timedelta

from booking.services import get_client_ip, send_contact_email_message
from django.db.models.functions import Cast, Concat
from django.db.models import DateTimeField, Value


class HomeView(TemplateView):
    """Главная страница"""

    template_name = "booking/home.html"


class AboutView(TemplateView):
    """О нас"""

    template_name = "booking/history_restaurant.html"


class ContactsView(TemplateView):
    """Контакты"""

    template_name = "booking/contacts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = 'Контакты ресторана "Гурман"'
        return context


# СТОЛЫ


class TableListView(LoginRequiredMixin, ListView):

    model = Table
    template_name = "booking/table_list.html"
    context_object_name = "tables"
    ordering = ["number"]

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not (
            user.has_perm("booking.administrate_tables")
            or user.has_perm("booking.super_administrate_tables")
            or user.is_superuser
        ):
            raise PermissionDenied("Доступ ограничен.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        status = super().get_queryset()

        active = self.request.GET.get("active")
        if active == "1":
            status = status.filter(is_active=True)
        elif active == "0":
            status = status.filter(is_active=False)
        return status


class TableCreateView(LoginRequiredMixin, CreateView):

    model = Table
    form_class = TableForm
    template_name = "booking/table_form.html"
    success_url = reverse_lazy("booking:table_list")

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not (
            user.has_perm("booking.administrate_tables")
            or user.has_perm("booking.super_administrate_tables")
            or user.is_superuser
        ):
            raise PermissionDenied("Доступ ограничен.")
        return super().dispatch(request, *args, **kwargs)


class TableDetailView(LoginRequiredMixin, DetailView):

    model = Table
    template_name = "booking/table_detail.html"
    context_object_name = "table"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not (
            user.has_perm("booking.administrate_tables")
            or user.has_perm("booking.super_administrate_tables")
            or user.is_superuser
        ):
            raise PermissionDenied("Доступ ограничен.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        context["reservations"] = self.object.reservation_set.filter(
            status__in=["confirmed"],
            reservation_date__gte=today_start.date(),
            end_time__gt=now.time() if now.date() == today_start.date() else None,
        ).order_by("reservation_date", "start_time")

        context["today"] = timezone.now().date()
        return context


class TableUpdateView(LoginRequiredMixin, UpdateView):

    model = Table
    form_class = TableForm
    template_name = "booking/table_form.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not (
            user.has_perm("booking.administrate_tables")
            or user.has_perm("booking.super_administrate_tables")
            or user.is_superuser
        ):
            raise PermissionDenied("Доступ ограничен.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("booking:table_detail", args=[self.object.pk])


class TableDeleteView(LoginRequiredMixin, DeleteView):

    model = Table
    template_name = "booking/table_confirm_delete.html"
    success_url = reverse_lazy("booking:table_list")

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not (user.has_perm("booking.super_administrate_tables") or user.is_superuser):
            raise PermissionDenied("Доступ ограничен.")
        return super().dispatch(request, *args, **kwargs)


# БРОНИРОВАНИЯ


class BookingListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "booking/booking_list.html"
    context_object_name = "reservations"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not (user.is_superuser or user.has_perm("booking.administrate_tables")):
            queryset = queryset.filter(user=user)

        filter_type = self.request.GET.get("filter", "future")
        today_start = timezone.make_aware(datetime.combine(timezone.now().date(), datetime.min.time()))

        if filter_type == "past":
            queryset = queryset.filter(reservation_date__lt=today_start)
        elif filter_type == "all":
            pass
        else:
            queryset = queryset.filter(reservation_date__gte=today_start)
        return queryset.annotate(
            start_dt=Cast(
                Concat("reservation_date", Value(" "), "start_time"),
                output_field=DateTimeField(),
            )
        ).order_by("start_dt")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.request.GET.get("filter", "future")
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):

    model = Reservation
    template_name = "booking/booking_detail.html"
    context_object_name = "booking"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["reservations"] = Reservation.objects.filter(
            table=self.object.table,
            status__in=["confirmed"],
            reservation_date__gte=timezone.now().date(),
        ).order_by("reservation_date", "start_time")
        ctx["today"] = timezone.now().date()
        return ctx


class BookingStartView(LoginRequiredMixin, FormView):
    template_name = "booking/booking_start.html"
    form_class = BookingParametersForm

    def form_valid(self, form):

        self.request.session["booking_params"] = {
            "reservation_date": form.cleaned_data["reservation_date"].isoformat(),
            "start_time": form.cleaned_data["start_time"].isoformat(),
            "guests_count": form.cleaned_data["guests_count"],
            "duration": form.cleaned_data["duration"],
        }
        return redirect("booking:table_selection")


class TableSelectionView(LoginRequiredMixin, ListView):
    template_name = "booking/table_selection.html"
    context_object_name = "tables"

    def get_queryset(self):
        booking_params = self.request.session.get("booking_params")
        if not booking_params:
            return redirect("booking:booking_start")

        reservation_date = datetime.strptime(booking_params["reservation_date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(booking_params["start_time"], "%H:%M:%S").time()
        guests_count = booking_params["guests_count"]
        duration = booking_params["duration"]

        start_dt = timezone.make_aware(datetime.combine(reservation_date, start_time))
        end_dt = start_dt + timedelta(hours=duration)

        self.booking_params = {
            "reservation_date": reservation_date,
            "start_time": start_time,
            "end_time": end_dt.time(),
            "duration": duration,
            "guests_count": guests_count,
        }

        busy = Reservation.objects.filter(
            reservation_date=reservation_date,
            status="confirmed",
            start_time__lt=end_dt.time(),
            end_time__gt=start_time,
        ).values_list("table_id", flat=True)

        return Table.objects.filter(
            is_active=True,
            min_guests__lte=guests_count,
            max_guests__gte=guests_count,
        ).exclude(id__in=busy)


class BookingConfirmView(LoginRequiredMixin, CreateView):

    model = Reservation
    fields = ["special_requests"]
    template_name = "booking/booking_confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        booking_params = self.request.session.get("booking_params")
        table_id = self.kwargs.get("table_id")

        if booking_params and table_id:
            context["booking_params"] = booking_params
            context["table"] = get_object_or_404(Table, id=table_id)

            reservation_date = datetime.strptime(booking_params["reservation_date"], "%Y-%m-%d").date()
            start_time = datetime.strptime(booking_params["start_time"], "%H:%M:%S").time()
            duration = int(booking_params["duration"])

            start_datetime = timezone.make_aware(datetime.combine(reservation_date, start_time))
            end_datetime = start_datetime + timedelta(hours=duration)

            context["start_time"] = start_time
            context["end_time"] = end_datetime.time()

        return context

    def form_valid(self, form):

        booking_params = self.request.session.get("booking_params")
        table_id = self.kwargs.get("table_id")

        if not booking_params or not table_id:
            form.add_error(None, "Данные бронирования не найдены. Пожалуйста, начните процесс заново.")
            return self.form_invalid(form)

        form.instance.user = self.request.user
        form.instance.status = "confirmed"
        form.instance.reservation_date = datetime.strptime(booking_params["reservation_date"], "%Y-%m-%d").date()
        form.instance.start_time = datetime.strptime(booking_params["start_time"], "%H:%M:%S").time()
        form.instance.guests_count = int(booking_params["guests_count"])
        form.instance.duration = int(booking_params["duration"])
        form.instance.table_id = table_id

        start_datetime = timezone.make_aware(
            datetime.combine(form.instance.reservation_date, form.instance.start_time)
        )
        end_datetime = start_datetime + timedelta(hours=form.instance.duration)
        form.instance.end_time = end_datetime.time()

        if "booking_params" in self.request.session:
            del self.request.session["booking_params"]

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("booking:booking_detail", kwargs={"pk": self.object.pk})


class BookingStatusUpdateView(LoginRequiredMixin, RedirectView):

    pattern_name = "booking:booking_detail"

    def get_redirect_url(self, *args, **kwargs):
        booking = get_object_or_404(Reservation, pk=kwargs["pk"])
        action = self.request.GET.get("action")
        user = self.request.user

        if booking.user != user and not (user.is_superuser or user.has_perm("booking.change_booking")):
            messages.error(self.request, "Можно изменять только свои бронирования.")
            return reverse("booking:booking_detail", kwargs={"pk": kwargs["pk"]})
        allowed = {
            "cancel": ("confirmed",),
            "complete": ("confirmed",),
            "no_show": ("confirmed",),
        }

        if action not in allowed:
            messages.warning(self.request, "Некорректное действие.")
            return reverse("booking:booking_detail", kwargs={"pk": kwargs["pk"]})

        if booking.status not in allowed[action]:
            messages.info(
                self.request, f"Действие «{action}» недоступно для статуса «{booking.get_status_display()}»."
            )
            return reverse("booking:booking_detail", kwargs={"pk": kwargs["pk"]})

            # меняем статус
        status_map = {"cancel": "canceled", "complete": "completed", "no_show": "no_show"}
        booking.status = status_map[action]
        booking.save(update_fields=["status"])
        messages.success(self.request, f"Статус изменён на «{booking.get_status_display()}».")

        return reverse("booking:booking_detail", kwargs={"pk": kwargs["pk"]})


class BookingDeleteView(LoginRequiredMixin, DeleteView):

    model = Reservation
    template_name = "booking/booking_confirm_delete.html"
    context_object_name = "booking"
    success_url = reverse_lazy("booking:booking_list")


# ОБРАТНАЯ СВЯЗЬ


class FeedbackCreateView(SuccessMessageMixin, CreateView):
    model = Feedback
    form_class = FeedbackCreateForm
    success_message = "Ваше письмо успешно отправлено администрации сайта"
    template_name = "booking/contacts.html"
    extra_context = {"title": "Контактная форма"}
    success_url = reverse_lazy("booking:home")

    def form_valid(self, form):
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.ip_address = get_client_ip(self.request)
            if self.request.user.is_authenticated:
                feedback.user = self.request.user
            send_contact_email_message(
                feedback.subject, feedback.email, feedback.content, feedback.ip_address, feedback.user_id
            )
        return super().form_valid(form)
