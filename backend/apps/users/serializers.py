"""DarsPro — users serializerlari."""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Profil ko'rinishi (GET/PATCH /me)."""

    effective_plan = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "telegram_id",
            "auth_provider",
            "plan",
            "effective_plan",
            "plan_expires_at",
            "is_staff",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "auth_provider",
            "plan",
            "plan_expires_at",
            "is_staff",
            "created_at",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """Email + parol bilan ro'yxatdan o'tish."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Email orqali login (USERNAME_FIELD allaqachon email)."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["plan"] = user.effective_plan
        return token


# --- Ijtimoiy / telefon auth ---------------------------------------------
class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class TelegramAuthSerializer(serializers.Serializer):
    """Telegram Login Widget payload'i. `hash` xom dictdan tekshiriladi."""

    id = serializers.IntegerField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    photo_url = serializers.CharField(required=False, allow_blank=True)
    auth_date = serializers.IntegerField()
    hash = serializers.CharField()


def _normalize_uz_phone(value):
    """+998XXXXXXXXX shakliga keltiradi (probel/chiziqchalarni olib tashlaydi)."""
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits.startswith("998") and len(digits) == 12:
        return "+" + digits
    if len(digits) == 9:  # mahalliy 9 xonali
        return "+998" + digits
    raise serializers.ValidationError("Telefon raqami noto'g'ri (+998XXXXXXXXX).")


class OtpSendSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        return _normalize_uz_phone(value)


class OtpVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.RegexField(r"^\d{6}$")

    def validate_phone(self, value):
        return _normalize_uz_phone(value)
