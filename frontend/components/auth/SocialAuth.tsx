"use client";

import { TriangleAlert } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/store";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
const TG_BOT = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME;

type GoogleId = {
  accounts: {
    id: {
      initialize: (cfg: {
        client_id: string;
        callback: (r: { credential: string }) => void;
      }) => void;
      renderButton: (el: HTMLElement, opts: Record<string, unknown>) => void;
    };
  };
};

declare global {
  interface Window {
    google?: GoogleId;
    onTelegramAuth?: (user: Record<string, unknown>) => void;
  }
}

/** Google + Telegram + telefon (OTP) bilan kirish. login va register sahifalari
 *  bir xil komponentni qayta ishlatadi. onSuccess muvaffaqiyatdan keyin chaqiriladi. */
export function SocialAuth({ onSuccess }: { onSuccess: () => void }) {
  const { loginWithGoogle, loginWithTelegram, sendOtp, verifyOtp, loading } =
    useAuth();
  const [error, setError] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const googleRef = useRef<HTMLDivElement>(null);
  const tgRef = useRef<HTMLDivElement>(null);

  // — Google Identity Services —
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !googleRef.current) return;
    const mount = googleRef.current;
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => {
      const g = window.google;
      if (!g) return;
      g.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID as string,
        callback: async (resp) => {
          try {
            await loginWithGoogle(resp.credential);
            onSuccess();
          } catch (e) {
            setError(e instanceof Error ? e.message : "Xatolik");
          }
        },
      });
      g.accounts.id.renderButton(mount, {
        theme: "outline",
        size: "large",
        width: 320,
        text: "continue_with",
      });
    };
    document.body.appendChild(script);
    return () => {
      script.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // — Telegram Login Widget —
  useEffect(() => {
    if (!TG_BOT || !tgRef.current) return;
    const mount = tgRef.current;
    window.onTelegramAuth = async (user) => {
      try {
        await loginWithTelegram(user);
        onSuccess();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Xatolik");
      }
    };
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", TG_BOT as string);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-userpic", "false");
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    mount.appendChild(script);
    return () => {
      script.remove();
      delete window.onTelegramAuth;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSendOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await sendOtp(phone);
      setOtpSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xatolik");
    }
  }

  async function onVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await verifyOtp(phone, code);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xatolik");
    }
  }

  return (
    <div className="mt-6 space-y-4">
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="h-px flex-1 bg-border" />
        yoki
        <span className="h-px flex-1 bg-border" />
      </div>

      {error && (
        <p className="flex items-center gap-2 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          <TriangleAlert size={15} /> {error}
        </p>
      )}

      {GOOGLE_CLIENT_ID && (
        <div ref={googleRef} className="flex justify-center" />
      )}
      {TG_BOT && <div ref={tgRef} className="flex justify-center" />}

      {/* Telefon (SMS kod) bilan kirish */}
      {!otpSent ? (
        <form onSubmit={onSendOtp} className="space-y-2">
          <Label htmlFor="otp-phone">Telefon raqami</Label>
          <div className="flex gap-2">
            <Input
              id="otp-phone"
              type="tel"
              inputMode="tel"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+998 90 123 45 67"
            />
            <Button type="submit" variant="secondary" disabled={loading}>
              Kod olish
            </Button>
          </div>
        </form>
      ) : (
        <form onSubmit={onVerifyOtp} className="space-y-2">
          <Label htmlFor="otp-code">SMS kod</Label>
          <div className="flex gap-2">
            <Input
              id="otp-code"
              inputMode="numeric"
              maxLength={6}
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="6 xonali kod"
            />
            <Button type="submit" disabled={loading}>
              {loading && <Spinner size={16} />}
              Tasdiqlash
            </Button>
          </div>
          <button
            type="button"
            className="text-xs text-muted-foreground underline"
            onClick={() => {
              setOtpSent(false);
              setCode("");
            }}
          >
            Raqamni o'zgartirish
          </button>
        </form>
      )}
    </div>
  );
}
