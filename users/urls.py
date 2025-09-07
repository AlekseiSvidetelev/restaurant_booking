from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView

from users.apps import UsersConfig

from users.views import (
    UserCreateView,
    email_verification,
    CustomPasswordResetRequestView,
    CustomPasswordResetConfirmView,
    UserListView,
    UserProfileView,
    UserProfileUpdateView,
)

app_name = UsersConfig.name

urlpatterns = [
    path("register/", UserCreateView.as_view(), name="register"),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout_confirm/", LoginView.as_view(template_name="users/logout_confirm.html"), name="logout_confirm"),
    path("logout/", LogoutView.as_view(next_page="mailings:home"), name="logout"),
    path("email_confirm/<str:token>/", email_verification, name="email_confirm"),
    path("password_reset_request/", CustomPasswordResetRequestView.as_view(), name="password_reset_request"),
    path(
        "password_reset_sent/",
        TemplateView.as_view(template_name="users/password_reset_sent.html"),
        name="password_reset_sent",
    ),
    path(
        "password_reset_confirm/<str:token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"
    ),
    path(
        "password_reset_complete/",
        TemplateView.as_view(template_name="users/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("users/", UserListView.as_view(), name="user_list"),
    path("profile/", UserProfileView.as_view(template_name="users/profile.html"), name="profile"),
    path(
        "profile/update/",
        UserProfileUpdateView.as_view(template_name="users/profile_update.html"),
        name="profile_update",
    ),
]
