"""DarsPro — /api/auth/ marshrutlari."""
from django.urls import path

from .auth_views import (
    GoogleAuthView,
    OtpSendView,
    OtpVerifyView,
    TelegramAuthView,
)
from .views import (
    LoginView,
    LogoutView,
    RefreshView,
    RegisterView,
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("refresh", RefreshView.as_view(), name="refresh"),
    path("logout", LogoutView.as_view(), name="logout"),
    # Ijtimoiy / telefon auth
    path("google", GoogleAuthView.as_view(), name="google"),
    path("telegram", TelegramAuthView.as_view(), name="telegram"),
    path("otp/send", OtpSendView.as_view(), name="otp-send"),
    path("otp/verify", OtpVerifyView.as_view(), name="otp-verify"),
]
