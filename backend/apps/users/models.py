"""DarsPro — User va Subscription modellari."""
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class Plan(models.TextChoices):
    FREE = "free", "Bepul"
    START = "start", "Start"
    PRO = "pro", "Pro"
    MAX = "max", "Max"


class AuthProvider(models.TextChoices):
    EMAIL = "email", "Email"
    GOOGLE = "google", "Google"
    TELEGRAM = "telegram", "Telegram"
    PHONE = "phone", "Telefon"


class User(AbstractBaseUser, PermissionsMixin):
    """Maxsus foydalanuvchi modeli — UUID PK, email orqali kirish."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True, unique=True)
    telegram_id = models.CharField(
        max_length=64, null=True, blank=True, unique=True
    )
    auth_provider = models.CharField(
        max_length=16, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )
    plan = models.CharField(max_length=8, choices=Plan.choices, default=Plan.FREE)
    plan_expires_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # createsuperuser faqat email + parol so'raydi

    class Meta:
        db_table = "users_user"

    def __str__(self):
        return self.email

    @property
    def effective_plan(self):
        """Tarif muddati o'tgan bo'lsa free hisoblanadi."""
        from django.utils import timezone

        if self.plan == Plan.FREE:
            return Plan.FREE
        if self.plan_expires_at and self.plan_expires_at < timezone.now():
            return Plan.FREE
        return self.plan


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    EXPIRED = "expired", "Muddati o'tgan"
    CANCELLED = "cancelled", "Bekor qilingan"


class Subscription(models.Model):
    """Obuna yozuvlari. O'zgarganda signal user.plan ni sinxronlaydi (ADR #5)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.CharField(
        max_length=8,
        choices=[c for c in Plan.choices if c[0] != Plan.FREE],
    )
    status = models.CharField(
        max_length=10,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    payment_ref = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        db_table = "users_subscription"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user.email} — {self.plan} ({self.status})"
