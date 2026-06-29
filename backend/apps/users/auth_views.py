"""DarsPro — ijtimoiy / telefon auth provayderlari (Google, Telegram, SMS OTP).

Har bir view oxirida `_tokens_for(user)` orqali JWT beradi va `RegisterView`
bilan bir xil `{user, tokens}` javob qaytaradi — frontend store bitta yo'lni
qayta ishlatadi. Parolsiz (ijtimoiy/telefon) foydalanuvchilar `create_user(...,
password=None)` orqali yaratiladi (set_unusable_password).
"""
import hashlib
import hmac
import logging
import secrets
import time

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import AuthProvider, User
from .serializers import (
    GoogleAuthSerializer,
    OtpSendSerializer,
    OtpVerifySerializer,
    TelegramAuthSerializer,
    UserSerializer,
)
from .sms import get_sms_backend
from .views import _tokens_for

logger = logging.getLogger("apps")


def _auth_response(user, created=False):
    """RegisterView bilan bir xil javob shakli."""
    return Response(
        {"user": UserSerializer(user).data, "tokens": _tokens_for(user)},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


class _AuthBase(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


# --- Google ---------------------------------------------------------------
class GoogleAuthView(_AuthBase):
    """POST /api/auth/google — Google id_token bilan kirish."""

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["id_token"]

        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": "Google auth sozlanmagan."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        from google.auth.transport import requests as g_requests
        from google.oauth2 import id_token as g_id_token

        try:
            info = g_id_token.verify_oauth2_token(
                token, g_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response(
                {"detail": "Yaroqsiz Google token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not info.get("email_verified"):
            return Response(
                {"detail": "Google email tasdiqlanmagan."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = info["email"].lower()
        name = info.get("name", "")
        # Mavjud email bo'lsa — bog'laymiz (dublikat yaratmaymiz).
        user = User.objects.filter(email=email).first()
        created = user is None
        if created:
            user = User.objects.create_user(
                email=email,
                password=None,
                full_name=name,
                auth_provider=AuthProvider.GOOGLE,
            )
        return _auth_response(user, created)


# --- Telegram -------------------------------------------------------------
def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    """Telegram Login Widget hash'ini tekshiradi (HMAC-SHA256)."""
    received_hash = data.get("hash", "")
    pairs = sorted(f"{k}={v}" for k, v in data.items() if k != "hash")
    data_check_string = "\n".join(pairs)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, received_hash)


class TelegramAuthView(_AuthBase):
    """POST /api/auth/telegram — Telegram Login Widget bilan kirish."""

    AUTH_TTL = 86400  # 24 soat

    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not settings.TELEGRAM_BOT_TOKEN:
            return Response(
                {"detail": "Telegram auth sozlanmagan."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # serializer faqat ma'lum maydonlarni qoldiradi; hash uchun xom dict kerak.
        raw = {k: str(v) for k, v in request.data.items() if v is not None}
        if not verify_telegram_auth(raw, settings.TELEGRAM_BOT_TOKEN):
            return Response(
                {"detail": "Telegram imzosi yaroqsiz."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if time.time() - data["auth_date"] > self.AUTH_TTL:
            return Response(
                {"detail": "Telegram sessiyasi eskirgan."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tg_id = str(data["id"])
        name = data.get("first_name") or data.get("username") or "Telegram"
        user = User.objects.filter(telegram_id=tg_id).first()
        created = user is None
        if created:
            user = User.objects.create_user(
                email=f"tg_{tg_id}@telegram.local",
                password=None,
                full_name=name,
                telegram_id=tg_id,
                auth_provider=AuthProvider.TELEGRAM,
            )
        return _auth_response(user, created)


# --- SMS OTP --------------------------------------------------------------
def _otp_key(phone):
    return f"otp:code:{phone}"


def _otp_rl_key(phone):
    return f"otp:rl:{phone}"


def _otp_attempts_key(phone):
    return f"otp:att:{phone}"


class OtpSendView(_AuthBase):
    """POST /api/auth/otp/send — telefon raqamiga 6 xonali kod yuboradi."""

    MAX_SENDS = 3  # bir telefon uchun oynadagi maksimal yuborish
    WINDOW = 600  # 10 daqiqa

    def post(self, request):
        serializer = OtpSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        sends = cache.get(_otp_rl_key(phone), 0)
        if sends >= self.MAX_SENDS:
            return Response(
                {"detail": "Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        code = f"{secrets.randbelow(900000) + 100000}"
        ttl = getattr(settings, "OTP_TTL_SEC", 300)
        cache.set(_otp_key(phone), make_password(code), ttl)
        cache.set(_otp_rl_key(phone), sends + 1, self.WINDOW)
        cache.delete(_otp_attempts_key(phone))

        try:
            get_sms_backend().send(phone, f"DarsPro tasdiqlash kodi: {code}")
        except Exception:  # noqa: BLE001 — SMS xatosi kirishni bloklamasin
            logger.exception("SMS yuborishda xato: %s", phone)
            return Response(
                {"detail": "SMS yuborib bo'lmadi. Keyinroq urinib ko'ring."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"sent": True}, status=status.HTTP_200_OK)


class OtpVerifyView(_AuthBase):
    """POST /api/auth/otp/verify — kodni tasdiqlab JWT beradi."""

    MAX_ATTEMPTS = 5
    WINDOW = OtpSendView.WINDOW

    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        stored = cache.get(_otp_key(phone))
        if not stored:
            return Response(
                {"detail": "Kod eskirgan yoki topilmadi. Qayta yuboring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempts = cache.get(_otp_attempts_key(phone), 0)
        if attempts >= self.MAX_ATTEMPTS:
            cache.delete(_otp_key(phone))
            return Response(
                {"detail": "Juda ko'p noto'g'ri urinish. Kodni qayta yuboring."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if not check_password(code, stored):
            cache.set(_otp_attempts_key(phone), attempts + 1, self.WINDOW)
            return Response(
                {"detail": "Kod noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST
            )

        cache.delete(_otp_key(phone))
        cache.delete(_otp_attempts_key(phone))
        cache.delete(_otp_rl_key(phone))

        user = User.objects.filter(phone=phone).first()
        created = user is None
        if created:
            user = User.objects.create_user(
                email=f"{phone}@phone.local",
                password=None,
                phone=phone,
                auth_provider=AuthProvider.PHONE,
            )
        return _auth_response(user, created)
