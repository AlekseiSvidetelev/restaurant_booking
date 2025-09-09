from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import FormView, CreateView, UpdateView, DetailView
from django.utils import timezone

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import secrets


from config.settings import EMAIL_HOST_USER

# from mailings.models import Mailings
from .forms import UserRegisterForm, PasswordResetRequestForm, CustomSetPasswordForm, UserProfileUpdateForm

from django.views.generic import ListView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from .models import User


class UserCreateView(CreateView):
    """Регистрация пользователя."""

    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email_confirm/{token}/"
        send_mail(
            subject="Подтверждение регистрации",
            message=f"Подтвердите регистрацию по ссылке: {url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        messages.success = (self.request, "Регистрация прошла успешно. Проверьте почту для подтверждения регистрации.")

        return super().form_valid(form)


def email_verification(request, token):
    """Подтверждение регистрации."""
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect("users:login")


class CustomPasswordResetRequestView(FormView):  # Переименован
    """Запрос на сброс пароля"""

    template_name = "users/password_reset_request.html"
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy("users:password_reset_sent")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = User.objects.get(email=email)
        token = secrets.token_urlsafe(16)
        user.reset_token = token
        user.reset_token_created = timezone.now()
        user.save()
        host = self.request.get_host()
        reset_url = f"http://{host}/users/password_reset_confirm/{token}/"

        send_mail(
            subject="Сброс пароля",
            message=f"Для сброса пароля перейдите по ссылке: {reset_url}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=render_to_string(
                "users/password_reset_email.html", {"reset_url": reset_url, "user": user, "expiration_hours": 24}
            ),
        )

        return super().form_valid(form)


class CustomPasswordResetConfirmView(FormView):
    """Подтверждение сброса пароля"""

    template_name = "users/password_reset_confirm.html"
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy("users:password_reset_complete")

    def get_user(self, token):
        return User.objects.get(reset_token=token)

    def dispatch(self, request, *args, **kwargs):
        """Проверка валидности токена"""
        self.token = kwargs["token"]
        self.user = self.get_user(self.token)
        if not self.user:
            return render(request, "users/password_reset_invalid.html")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Передача пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Добавление пользователя в контекст"""
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context

    def form_valid(self, form):
        """Обработка валидной формы"""
        token_age = timezone.now() - self.user.reset_token_created
        if token_age.total_seconds() > 24 * 3600:
            return render(self.request, "users/password_reset_expired.html")
        form.save()
        self.user.reset_token = None
        self.user.reset_token_created = None
        self.user.save()
        return super().form_valid(form)


class UserListView(ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.has_perm("users.can_view_all_users")

    def post(self, request, *args, **kwargs):
        """Обработка блокировки/разблокировки"""
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        user = User.objects.get(id=user_id)

        if action == "block":
            user.is_active = False
            user.save()
            messages.success(request, f"Пользователь {user.email} заблокирован")

        return redirect("users:user_list")


class UserProfileView(LoginRequiredMixin, DetailView):

    model = User
    template_name = "users/profile.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        return self.request.user

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     user = self.request.user
    #     context["mailings_count"] = Mailings.objects.filter(owner=user).count()
    #     context["active_mailings"] = Mailings.objects.filter(owner=user, status="started").count()
    #     return context


class UserProfileUpdateView(UpdateView):

    model = User
    form_class = UserProfileUpdateForm
    template_name = "users/profile_update.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user
