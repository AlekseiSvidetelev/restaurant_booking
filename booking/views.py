

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, DeleteView, FormView

from booking.forms import TableForm, BookingParametersForm
from booking.models import Reservation, Table
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta


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
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["today"] = timezone.now().date()
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
    ordering = ["-reservation_date", "-start_time"]


class BookingDetailView(DetailView):

    model = Reservation
    template_name = "booking/booking_detail.html"
    context_object_name = "booking"


class BookingStartView(FormView):
    template_name = 'booking/booking_start.html'
    form_class = BookingParametersForm

    def form_valid(self, form):
        # Сохраняем параметры в сессии
        self.request.session['booking_params'] = {
            'reservation_date': form.cleaned_data['reservation_date'].isoformat(),
            'start_time': form.cleaned_data['start_time'].isoformat(),
            'guests_count': form.cleaned_data['guests_count'],
            'duration': form.cleaned_data['duration'],
        }
        return redirect('booking:table_selection')


class TableSelectionView(ListView):
    template_name = 'booking/table_selection.html'
    context_object_name = 'tables'

    def get_queryset(self):
        # Получаем параметры из сессии
        booking_params = self.request.session.get('booking_params')
        if not booking_params:
            return redirect('booking:booking_start')

        # Преобразуем параметры
        reservation_date = datetime.strptime(booking_params['reservation_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(booking_params['start_time'], '%H:%M:%S').time()
        guests_count = booking_params['guests_count']
        duration = booking_params['duration']

        # Вычисляем время окончания
        start_datetime = timezone.make_aware(
            datetime.combine(reservation_date, start_time)
        )
        end_datetime = start_datetime + timedelta(hours=duration)
        end_time = end_datetime.time()

        # Сохраняем параметры в контекст
        self.booking_params = {
            'reservation_date': reservation_date,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'guests_count': guests_count
        }

        # Находим занятые столики
        booked_tables = Reservation.objects.filter(
            reservation_date=reservation_date,
            status__in=['pending', 'confirmed'],
        ).exclude(
            Q(end_time__lte=start_time) | Q(start_time__gte=end_time)
        ).values_list('table_id', flat=True)

        # Возвращаем свободные столики с достаточной вместимостью
        return Table.objects.filter(
            seats__gte=guests_count,
            is_active=True
        ).exclude(id__in=booked_tables)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.booking_params)
        return context


class BookingConfirmView(CreateView):
    model = Reservation
    fields = ['special_requests']  # Только особые пожелания
    template_name = 'booking/booking_confirm.html'

    def get_initial(self):
        initial = super().get_initial()
        # Получаем параметры из сессии
        booking_params = self.request.session.get('booking_params')
        table_id = self.kwargs.get('table_id')

        if booking_params and table_id:
            initial.update({
                'reservation_date': booking_params['reservation_date'],
                'start_time': booking_params['start_time'],
                'guests_count': booking_params['guests_count'],
                'duration': booking_params['duration'],
                'table': table_id
            })
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'pending'

        # Устанавливаем end_time
        reservation_date = form.cleaned_data['reservation_date']
        start_time = form.cleaned_data['start_time']
        duration = form.cleaned_data['duration']

        start_datetime = timezone.make_aware(
            datetime.combine(reservation_date, start_time)
        )
        end_datetime = start_datetime + timedelta(hours=duration)
        form.instance.end_time = end_datetime.time()

        # Очищаем сессию
        if 'booking_params' in self.request.session:
            del self.request.session['booking_params']

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('booking:booking_detail', kwargs={'pk': self.object.pk})



class BookingDeleteView(DeleteView):

    model = Reservation
    template_name = "booking/booking_confirm_delete.html"
    context_object_name = "booking"
    success_url = reverse_lazy("booking:booking_list")
