"""DarsPro — SMS yuborish gateway'i (OTP uchun).

`SMS_PROVIDER` env orqali backend tanlanadi:
  - console (default): kodni logga chiqaradi — dev/test uchun, tarmoq kerak emas.
  - eskiz: Eskiz.uz REST API (token-asosli) — prod uchun.

Yangi provayder qo'shish: `SmsBackend` interfeysini amalga oshiring va
`get_sms_backend()` ga ulang.
"""
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("apps")


class ConsoleSmsBackend:
    """SMS yubormaydi — kodni logga yozadi (dev/test)."""

    def send(self, phone: str, text: str) -> None:
        logger.info("SMS → %s: %s", phone, text)


class EskizSmsBackend:
    """Eskiz.uz (https://eskiz.uz) — O'zbekiston transactional SMS provayderi."""

    BASE = "https://notify.eskiz.uz/api"
    TOKEN_CACHE_KEY = "eskiz:token"

    def _token(self) -> str:
        token = cache.get(self.TOKEN_CACHE_KEY)
        if token:
            return token
        import requests

        resp = requests.post(
            f"{self.BASE}/auth/login",
            data={
                "email": settings.ESKIZ_EMAIL,
                "password": settings.ESKIZ_PASSWORD,
            },
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json()["data"]["token"]
        # Eskiz tokeni ~30 kun yashaydi; ehtiyot uchun 1 kun keshlaymiz.
        cache.set(self.TOKEN_CACHE_KEY, token, 60 * 60 * 24)
        return token

    def send(self, phone: str, text: str) -> None:
        import requests

        token = self._token()
        resp = requests.post(
            f"{self.BASE}/message/sms/send",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "mobile_phone": phone.lstrip("+"),
                "message": text,
                "from": settings.SMS_FROM,
            },
            timeout=10,
        )
        resp.raise_for_status()


def get_sms_backend():
    """Sozlamadagi `SMS_PROVIDER` bo'yicha backend qaytaradi."""
    provider = getattr(settings, "SMS_PROVIDER", "console")
    if provider == "eskiz":
        return EskizSmsBackend()
    return ConsoleSmsBackend()
