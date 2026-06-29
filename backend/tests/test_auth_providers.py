"""DarsPro — ijtimoiy / telefon auth provayderlari testlari (Phase 2)."""
import hashlib
import hmac
from unittest import mock

from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.users.models import AuthProvider, User

GGL = "apps.users.auth_views"


@override_settings(
    GOOGLE_CLIENT_ID="test-client",
    TELEGRAM_BOT_TOKEN="test-bot-token",
    SMS_PROVIDER="console",
)
class AuthProvidersTests(APITestCase):
    def setUp(self):
        cache.clear()

    # --- Google ---------------------------------------------------------
    def _patch_google(self, info):
        return mock.patch(
            "google.oauth2.id_token.verify_oauth2_token", return_value=info
        )

    def test_google_creates_and_links(self):
        info = {"email": "G@x.uz", "email_verified": True, "name": "G"}
        with self._patch_google(info):
            r1 = self.client.post(
                "/api/auth/google", {"id_token": "tok"}, format="json"
            )
        self.assertEqual(r1.status_code, 201)
        self.assertTrue(r1.data["tokens"]["access"])
        self.assertEqual(r1.data["user"]["auth_provider"], AuthProvider.GOOGLE)
        self.assertEqual(User.objects.filter(email="g@x.uz").count(), 1)

        # Ikkinchi marta — yangi user yaratilmaydi (link).
        with self._patch_google(info):
            r2 = self.client.post(
                "/api/auth/google", {"id_token": "tok"}, format="json"
            )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(User.objects.filter(email="g@x.uz").count(), 1)

    def test_google_bad_token(self):
        with mock.patch(
            "google.oauth2.id_token.verify_oauth2_token",
            side_effect=ValueError("bad"),
        ):
            r = self.client.post(
                "/api/auth/google", {"id_token": "x"}, format="json"
            )
        self.assertEqual(r.status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_google_unverified_email(self):
        info = {"email": "u@x.uz", "email_verified": False, "name": "U"}
        with self._patch_google(info):
            r = self.client.post(
                "/api/auth/google", {"id_token": "x"}, format="json"
            )
        self.assertEqual(r.status_code, 401)

    # --- Telegram -------------------------------------------------------
    @staticmethod
    def _tg_payload(bot_token="test-bot-token", auth_date=None, tamper=False):
        import time

        data = {
            "id": "55501",
            "first_name": "Ali",
            "username": "ali",
            "auth_date": str(int(auth_date if auth_date is not None else time.time())),
        }
        check = "\n".join(sorted(f"{k}={v}" for k, v in data.items()))
        secret = hashlib.sha256(bot_token.encode()).digest()
        data["hash"] = hmac.new(
            secret, check.encode(), hashlib.sha256
        ).hexdigest()
        if tamper:
            data["first_name"] = "Vali"  # hashdan keyin o'zgartiramiz
        return data

    def test_telegram_valid(self):
        r = self.client.post(
            "/api/auth/telegram", self._tg_payload(), format="json"
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["tokens"]["access"])
        u = User.objects.get(telegram_id="55501")
        self.assertEqual(u.auth_provider, AuthProvider.TELEGRAM)
        # Ikkinchi marta — link.
        r2 = self.client.post(
            "/api/auth/telegram", self._tg_payload(), format="json"
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(User.objects.filter(telegram_id="55501").count(), 1)

    def test_telegram_tampered(self):
        r = self.client.post(
            "/api/auth/telegram", self._tg_payload(tamper=True), format="json"
        )
        self.assertEqual(r.status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_telegram_stale(self):
        r = self.client.post(
            "/api/auth/telegram",
            self._tg_payload(auth_date=0),  # 1970 — eskirgan
            format="json",
        )
        self.assertEqual(r.status_code, 401)

    # --- SMS OTP --------------------------------------------------------
    def test_otp_send_and_verify(self):
        with mock.patch(f"{GGL}.secrets.randbelow", return_value=23456):
            s = self.client.post(
                "/api/auth/otp/send", {"phone": "901234567"}, format="json"
            )
        self.assertEqual(s.status_code, 200)
        v = self.client.post(
            "/api/auth/otp/verify",
            {"phone": "901234567", "code": "123456"},
            format="json",
        )
        self.assertEqual(v.status_code, 201)  # yangi user yaratildi
        u = User.objects.get(phone="+998901234567")
        self.assertEqual(u.auth_provider, AuthProvider.PHONE)
        self.assertTrue(v.data["tokens"]["access"])

    def test_otp_wrong_code(self):
        with mock.patch(f"{GGL}.secrets.randbelow", return_value=23456):
            self.client.post(
                "/api/auth/otp/send", {"phone": "901234567"}, format="json"
            )
        v = self.client.post(
            "/api/auth/otp/verify",
            {"phone": "901234567", "code": "000000"},
            format="json",
        )
        self.assertEqual(v.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_otp_expired(self):
        with mock.patch(f"{GGL}.secrets.randbelow", return_value=23456):
            self.client.post(
                "/api/auth/otp/send", {"phone": "901234567"}, format="json"
            )
        cache.delete("otp:code:+998901234567")  # muddati o'tganini simulatsiya
        v = self.client.post(
            "/api/auth/otp/verify",
            {"phone": "901234567", "code": "123456"},
            format="json",
        )
        self.assertEqual(v.status_code, 400)

    def test_otp_rate_limit(self):
        for _ in range(3):
            ok = self.client.post(
                "/api/auth/otp/send", {"phone": "901234567"}, format="json"
            )
            self.assertEqual(ok.status_code, 200)
        blocked = self.client.post(
            "/api/auth/otp/send", {"phone": "901234567"}, format="json"
        )
        self.assertEqual(blocked.status_code, 429)
