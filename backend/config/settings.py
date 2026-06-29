"""DarsPro — Django sozlamalari.

.env fayli orqali sozlanadi (django-environ). Sirlar .env.example da hujjatlangan.
"""
import sys
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Test rejimi: throttle o'chiriladi, lokal cache ishlatiladi (Redis shart emas)
TESTING = "test" in sys.argv

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
    ACCESS_TOKEN_LIFETIME_MIN=(int, 60),
    REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
)

# .env faylini o'qish (mavjud bo'lsa)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "daphne",  # ASGI server (runserver'ni almashtiradi)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Uchinchi tomon
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "channels",
    "drf_spectacular",
    "django_prometheus",
    # Loyiha applari
    "apps.users",
    "apps.content",
    "apps.sessions",
    "apps.admin_panel",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "config.middleware.RequestIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database ---
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://darspro:darspro@localhost:5432/darspro",
    ),
}

# --- Redis: channel layer + cache ---
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# DEV_LOCAL: Redis'siz lokal ishga tushirish (locmem cache + InMemory channel layer).
# Faqat dev/demo uchun — bitta jarayonda ishlaydi.
DEV_LOCAL = env.bool("DEV_LOCAL", default=False)
NO_REDIS = TESTING or DEV_LOCAL

if NO_REDIS:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        },
    }
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        },
    }

# --- Auth ---
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# So'rov tanasi hajmi chegarasi (DoS oldini olish)
DATA_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024  # 3MB

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Rate limiting — brute-force va spamdan himoya
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "240/min",
        "auth": "10/min",  # login/register/otp uchun qattiqroq (ScopedRateThrottle)
    },
}

if TESTING:
    # Testlarda rate-limiting o'chiriladi (rate=None -> throttle hech narsani bloklamaydi).
    # Kalitlar saqlanadi, aks holda view-darajadagi ScopedRateThrottle xato beradi.
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": None,
        "user": None,
        "auth": None,
    }

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("ACCESS_TOKEN_LIFETIME_MIN")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("REFRESH_TOKEN_LIFETIME_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- CORS ---
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

# --- i18n: faqat o'zbek (ADR #6) ---
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Media (rasmlar) ---
# Dev: lokal fayl tizimi. Prod: S3-mos storage (USE_S3=True bo'lsa) — quyida.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
MAX_UPLOAD_MB = env.int("MAX_UPLOAD_MB", default=5)
if TESTING:
    import tempfile

    MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="darspro_media_"))

# --- Storage backend ---
# USE_S3=True bo'lsa media fayllar S3-mos storage'ga yoziladi (django-storages).
# Sukut bo'yicha lokal FileSystemStorage (Django default STORAGES) ishlatiladi.
# Test rejimida hech qachon S3 ishlatilmaydi.
USE_S3 = env.bool("USE_S3", default=False) and not TESTING
if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="")
    # S3-mos provayderlar uchun (MinIO, Wasabi, DigitalOcean Spaces va h.k.)
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="") or None
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="") or None
    AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default=False)
    AWS_DEFAULT_ACL = None  # bucket policy boshqaradi
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }

# --- Email ---
# Dev: console backend (terminalga chiqaradi). Prod: SMTP env orqali ulanadi.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="DarsPro <no-reply@darspro.uz>"
)

# --- Auth provayderlari (Google / Telegram / SMS OTP) ---
# Bo'sh qoldirilsa tegishli endpoint 503 qaytaradi (sozlanmagan).
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_BOT_USERNAME = env("TELEGRAM_BOT_USERNAME", default="")
SMS_PROVIDER = env("SMS_PROVIDER", default="console")  # console | eskiz
ESKIZ_EMAIL = env("ESKIZ_EMAIL", default="")
ESKIZ_PASSWORD = env("ESKIZ_PASSWORD", default="")
SMS_FROM = env("SMS_FROM", default="4546")
OTP_TTL_SEC = env.int("OTP_TTL_SEC", default=300)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- API hujjat (drf-spectacular) ---
SPECTACULAR_SETTINGS = {
    "TITLE": "DarsPro API",
    "DESCRIPTION": "O'qituvchilar uchun o'yin platformasi — REST API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Enum nomlari to'qnashuvini oldini olish
    "ENUM_NAME_OVERRIDES": {
        "PlanEnum": "apps.users.models.Plan",
        "ContentStatusEnum": "apps.content.models.ContentStatus",
        "ContentSourceEnum": "apps.content.models.ContentSource",
        "SessionModeEnum": "apps.sessions.models.SessionMode",
        "SessionStatusEnum": "apps.sessions.models.SessionStatus",
    },
}

# --- Celery (vazifa navbati + beat) ---
from celery.schedules import crontab  # noqa: E402

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = TESTING  # testlarda sinxron ishlaydi (broker shart emas)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BEAT_SCHEDULE = {
    "reconcile-plans": {
        "task": "apps.users.tasks.reconcile_plans_task",
        "schedule": crontab(minute=0),  # har soat boshida
    },
    "cleanup-sessions": {
        "task": "apps.sessions.tasks.cleanup_sessions_task",
        "schedule": crontab(minute="*/30"),  # har 30 daqiqada
    },
}

# --- Logging ---
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOG_FORMAT = env("LOG_FORMAT", default="text")  # "json" -> structured
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name}: {message}",
            "style": "{",
        },
        "json": {
            "()": "config.middleware.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if LOG_FORMAT == "json" else "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Loyiha applari
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "consumers": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
if TESTING:
    # Testlarda log shovqinini kamaytirish
    LOGGING["root"]["level"] = "CRITICAL"

# --- Sentry (faqat SENTRY_DSN bo'lsa) ---
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN and not TESTING:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_RATE", default=0.0),
        send_default_pii=False,
        environment="production" if not DEBUG else "development",
    )

# --- Production hardening (faqat DEBUG=False, test bo'lmaganda) ---
if not DEBUG and not TESTING:
    if SECRET_KEY in ("insecure-dev-key-change-me", ""):
        raise RuntimeError(
            "Production'da xavfsiz SECRET_KEY o'rnating (.env -> SECRET_KEY)."
        )
    # Reverse-proxy (nginx) orqasidagi HTTPS'ni tan olish
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 yil
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
