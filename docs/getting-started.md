# Getting Started

**djbp_free** is a Django micro-SaaS boilerplate: authentication, billing, file
storage and an async video-processing pipeline, wired together so you can start
building your product on day one instead of assembling plumbing.

It runs with **zero external services**: SQLite, a console email backend and
inline (eager) task execution are the defaults. Each piece upgrades to a real
backend (Postgres, Cloudflare R2, Gmail SMTP, Redis + Celery, Stripe, Deepgram,
ElevenLabs, DeepSeek) by filling in environment variables.

## Stack

| Layer      | Choice                                             |
|------------|----------------------------------------------------|
| Framework  | Django 6.0, Python 3.12+                           |
| Auth       | django-allauth 65 — social login only (Google/Meta)|
| Frontend   | Tailwind CSS v4 + daisyUI 5 + HTMX                 |
| Database   | SQLite (default) or Postgres                       |
| Storage    | Cloudflare R2 (S3-compatible), local disk fallback |
| Billing    | Lemon Squeezy (primary) / Stripe, credits ledger   |
| Jobs       | Celery + Redis (eager inline mode in dev)          |
| Pipeline   | Deepgram transcribe -> DeepSeek agent -> ElevenLabs TTS -> ffmpeg render |

## Prerequisites

- **Python 3.12+** (3.14 works; see notes below)
- **Node.js 18+** — only needed once, to build the Tailwind/daisyUI CSS
- Nothing else. No Docker, no Postgres, no Redis for local development.

## Install

```bash
# 1. Clone and enter the project
cd djbp_free

# 2. Create a virtualenv and install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Create your environment file from the template
cp .env.example .env

# 4. Build the frontend CSS (Tailwind + daisyUI)
cd theme/static_src
npm install
npm run build          # one-time production build
# npm run dev          # watch mode while you edit templates
cd ../..

# 5. Set up the database and static files
python manage.py migrate

# 6. Run it
python manage.py runserver
```

Open http://localhost:8000 — you should see the landing page, and
http://localhost:8000/accounts/login/ the login page.

## Smoke test

```bash
python manage.py check    # zero issues expected
python manage.py test     # the shipped test suite
```

## What works out of the box

- Landing page, pricing page, login page, dashboard (all template placeholders
  you replace with your product)
- Google sign-in — works as soon as `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
  are set (see [Configuration](configuration.md))
- Credit-account billing skeleton — pricing page renders, checkouts appear once
  a gateway is configured

## Notes for contributors

- **`.env` is loaded via python-dotenv at settings import time.** Shell-exported
  variables take precedence over `.env` (override=False) — unset a var in your
  shell if you want the `.env` value to apply.
- **`DEBUG=True` is required for local development.** With `DEBUG=False` the
  settings force SSL redirects and secure cookies, which break `runserver`.
- **Tailwind v4 is CSS-first.** `theme/static_src/tailwind.config.js` (if
  present) is a dead v3 artifact; class sources are declared in
  `theme/static_src/src/styles.css` via `@source`. After editing templates with
  new utility classes, rebuild (`npm run build`) or run watch mode.
- **Static files in production use a manifest.** Before deploys and before
  running tests against prod-like settings, run `python manage.py collectstatic
  --noinput` (tests can also override staticfiles to plain `StaticFilesStorage`).
- **Port 8000 may be taken** on shared machines — `python manage.py runserver
  8001` works the same.

## Next steps

- [Configuration](configuration.md) — every environment variable and how to get
  the real credentials
- [Architecture](architecture.md) — how the apps fit together
- [Deployment](deployment.md) — production checklist
