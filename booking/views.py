
from django.contrib.messages.views import SuccessMessageMixin

from django.db.models import Q

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, DeleteView, FormView

from booking.forms import TableForm, BookingParametersForm, FeedbackCreateForm
from booking.models import Reservation, Table, Feedback
from django.utils import timezone
from datetime import datetime, timedelta

from booking.services import get_client_ip, send_contact_email_message


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


class TableListView(ListView):

    model = Table
    template_name = "booking/table_list.html"
    context_object_name = "tables"
    ordering = ["number"]

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.GET.get("active")
        if active == "1":
            qs = qs.filter(is_active=True)
        elif active == "0":
            qs = qs.filter(is_active=False)
        return qs


class TableCreateView(CreateView):

    model = Table
    form_class = TableForm
    template_name = "booking/table_form.html"
    success_url = reverse_lazy("booking:table_list")


class TableDetailView(DetailView):

    model = Table
    template_name = "booking/table_detail.html"
    context_object_name = "table"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reservations'] = self.object.reservation_set.filter(
            status__in=['reserved', 'pending'],
            reservation_date__gte=timezone.now().date()
        ).order_by('reservation_date', 'start_time')

        ctx['today'] = timezone.now().date()
        return ctx


class TableUpdateView(UpdateView):

    model = Table
    form_class = TableForm
    template_name = "booking/table_form.html"
    success_url = reverse_lazy("booking:table_list")

    def get_success_url(self):
        return reverse("booking:table_detail", args={self.kwargs.get("pk")})


class TableDeleteView(DeleteView):

    model = Table
    template_name = "booking/table_confirm_delete.html"
    success_url = reverse_lazy("booking:table_list")


class BookingListView(ListView):

    model = Reservation
    template_name = "booking/booking_list.html"
    context_object_name = "reservations"
    ordering = ["reservation_date", "-start_time"]


class BookingDetailView(DetailView):

    model = Reservation
    template_name = "booking/booking_detail.html"
    context_object_name = "booking"


class BookingStartView(FormView):
    template_name = "booking/booking_start.html"
    form_class = BookingParametersForm

    def form_valid(self, form):
        # Сохраняем параметры в сессии
        self.request.session["booking_params"] = {
            "reservation_date": form.cleaned_data["reservation_date"].isoformat(),
            "start_time": form.cleaned_data["start_time"].isoformat(),
            "guests_count": form.cleaned_data["guests_count"],
            "duration": form.cleaned_data["duration"],
        }
        return redirect("booking:table_selection")


class TableSelectionView(ListView):
    template_name = "booking/table_selection.html"
    context_object_name = "tables"

    def get_queryset(self):
        booking_params = self.request.session.get("booking_params")
        if not booking_params:
            return redirect("booking:booking_start")

        reservation_date = datetime.strptime(
            booking_params["reservation_date"], "%Y-%m-%d"
        ).date()
        start_time = datetime.strptime(
            booking_params["start_time"], "%H:%M:%S"
        ).time()
        guests_count = booking_params["guests_count"]
        duration = booking_params["duration"]

        start_dt = timezone.make_aware(
            datetime.combine(reservation_date, start_time)
        )
        end_dt = start_dt + timedelta(hours=duration)

        # сохраним в контекст (если нужно)
        self.booking_params = {
            "reservation_date": reservation_date,
            "start_time": start_time,
            "end_time": end_dt.time(),
            "duration": duration,
            "guests_count": guests_count,
        }

        busy = (
            Reservation.objects.filter(
                reservation_date=reservation_date,
                status__in=["pending", "confirmed"],
            )
            .exclude(
                Q(end_time__lte=start_time) | Q(start_time__gte=end_dt.time())
            )
            .values_list("table_id", flat=True)
        )

        return Table.objects.filter(
            is_active=True,
            min_guests__lte=guests_count,
            max_guests__gte=guests_count,
        ).exclude(id__in=busy)


class BookingConfirmView(CreateView):
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
        form.instance.status = "pending"
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


class BookingDeleteView(DeleteView):

    model = Reservation
    template_name = "booking/booking_confirm_delete.html"
    context_object_name = "booking"
    success_url = reverse_lazy("booking:booking_list")


class FeedbackCreateView(SuccessMessageMixin, CreateView):
    model = Feedback
    form_class = FeedbackCreateForm
    success_message = 'Ваше письмо успешно отправлено администрации сайта'
    template_name = 'booking/contacts.html'
    extra_context = {'title': 'Контактная форма'}
    success_url = reverse_lazy('booking:home')

    def form_valid(self, form):
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.ip_address = get_client_ip(self.request)
            if self.request.user.is_authenticated:
                feedback.user = self.request.user
            send_contact_email_message(feedback.subject, feedback.email, feedback.content, feedback.ip_address, feedback.user_id)
        return super().form_valid(form)
