# DarsPro 🎮

O'zbekiston maktab o'qituvchilari uchun **o'yin platformasi** — tayyor o'yinlar va
kontent kutubxonasi. O'qituvchilar savollarini kiritadi, o'yin enginelari original
o'yinlar yaratadi, sinf jonli (real-time) rejimda o'ynaydi.

[![CI](https://github.com/Viltrumlik/DarsPro/actions/workflows/ci.yml/badge.svg)](https://github.com/Viltrumlik/DarsPro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Til:** faqat o'zbek tili · **Platforma:** web (online-only) · **Auditoriya:** 1–11 sinf o'qituvchilari

**English summary.** DarsPro is a classroom game platform for school teachers in Uzbekistan
(grades 1–11, Uzbek-language UI). Teachers enter their own questions into one of 11 game
engines (quiz, matching, flashcards, memory, spin wheel, sort order, fill in the blank,
crossword, word search, true/false, poll) or pick ready-made content from a library, then
play solo or run a live class session: students join with a short code and no account, with
a real-time leaderboard over WebSockets. Stack: Django 5 + DRF + Channels + Celery +
PostgreSQL + Redis on the backend, Next.js 14 + TypeScript + Tailwind on the frontend.
Setup steps are under *Tez boshlash* (Quick start) below.

---

## Imkoniyatlar

- 🔐 **Auth** — email + parol (JWT). Google/Telegram/OTP keyingi fazada.
- 📚 **Kontent kutubxonasi** — sinf / fan / mavzu bo'yicha filtr, paginatsiya.
- 🛠 **Builder** — 11 ta o'yin engine: Quiz, Matching, Flashcard, Memory, Spin Wheel,
  Sort Order, Fill Blank, Crossword, Word Search, True/False, Poll. Har biri Play + Builder rejimida.
- 🎓 **Rejimlar** — yakka (solo), sinf (live), juft, jamoa.
- 📡 **Real-time sinf** — WebSocket (Django Channels): host boshqaradi, o'quvchilar
  kod bilan akkauntsiz qo'shiladi, jonli reyting, medallar.
- 🧑‍💼 **Admin panel** — kontent review (approve/reject), manual tarif berish.
- 💳 **Tariflar** — free / start / pro / max; oylik yaratish kvotasi, sinf hajmi limiti.
- 📊 **Analitika** — sessiya hisobotlari, statistika.
- ⚙️ **Operatsion** — health endpointlar, Celery + Beat (davriy ishlar), Redis caching, logging.

## Tech stack

| Qatlam | Texnologiyalar |
|--------|----------------|
| **Backend** | Django 5, DRF, Django Channels, Celery, PostgreSQL, Redis, SimpleJWT |
| **Frontend** | Next.js 14 (App Router), TypeScript, TailwindCSS, Framer Motion, Zustand |
| **Test/CI** | Django test (39), Vitest (47), Playwright (e2e smoke), GitHub Actions |
| **Infra** | Docker Compose (db, redis, web, worker, beat), S3-mos storage (media) |

## Struktura

```
darspro/
├── backend/    # Django: apps/{users,content,sessions,admin_panel} + consumers/ (WS)
├── frontend/   # Next.js: app/, components/engines/, components/ui/, lib/
├── .github/    # CI workflow
└── CLAUDE.md   # to'liq spetsifikatsiya (yagona haqiqat manbai)
```

## Tez boshlash

### Backend
```bash
cd backend
cp .env.example .env
docker compose up -d db redis
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py loaddata grades subjects engines topics sample_items
docker compose run --rm web python manage.py createsuperuser
docker compose up web worker beat        # API :8000, Celery worker + beat
```
Docker'siz (lokal Postgres + Redis kerak): `pip install -r requirements.txt && python manage.py migrate && python manage.py runserver`.

### Frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                              # http://localhost:3000
```

## API hujjat

Server ishga tushgach: **Swagger UI** → `http://localhost:8000/api/docs`
(OpenAPI sxema: `/api/schema`). Health: `/api/health`, `/api/health/ready`.

## Testlar

```bash
# Backend (DB serveri shart emas — SQLite + InMemory channel layer)
cd backend && DATABASE_URL="sqlite:////tmp/t.sqlite3" python manage.py test tests

# Frontend
cd frontend && npm run test && npm run build
```

## Arxitektura qarorlari (ADR)

1. **Online-only** — kontent yuklab olinmaydi (tarqalishni oldini olish).
2. **Engine data = JSONB** — yangi engine uchun migration kerak emas.
3. **O'quvchilar akkauntsiz** — `GameParticipant` faqat ism + ball.
4. **join_code** — `DRS-XXXX` (proyektorda ko'rsatish uchun qisqa).
5. **user.plan denormalizatsiya** — obuna o'zgarganda signal sinxronlaydi.
6. **Faqat o'zbek tili** — i18n yo'q (MVP soddaligi).

To'liq spetsifikatsiya: [`CLAUDE.md`](CLAUDE.md).
Owner: @Viltrumlik

## Litsenziya / License

[MIT](LICENSE) litsenziyasi asosida tarqatiladi. Released under the [MIT License](LICENSE).
