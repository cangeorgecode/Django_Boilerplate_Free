# Deployment

The app deploys like any Django project: gunicorn + nginx on a VPS (Linode,
DigitalOcean, Hetzner, ...). SQLite is fine for a single server; switch to
Postgres when you add workers or see write contention.

## Pre-flight checklist

1. **Real `SECRET_KEY`** — the dev fallback is insecure:
   `python -c "import secrets; print(secrets.token_urlsafe(64))"`
2. **`DEBUG=False`** in `.env` — this enables the production security block
   (HSTS, secure cookies, SSL redirect, frame-deny).
3. **`BASE_URL`** — your real https domain (no trailing slash).
4. **`ALLOWED_HOSTS`** — your domain (comma-separated).
5. **`DB_ENGINE=postgres`** + credentials (recommended) or keep SQLite.
6. **R2, Stripe/Lemon, email, pipeline keys** — see
   [Configuration](configuration.md).
7. **OAuth redirect URIs** — add `https://<your-domain>/accounts/google/login/callback/`
   (and the facebook equivalent, if used) to the provider consoles.

## Build and collect static

```bash
cd theme/static_src && npm ci && npm run build && cd ../..
source .venv/bin/activate
python manage.py collectstatic --noinput
python manage.py migrate
```

WhiteNoise serves static files in production (manifest storage), so no nginx
static alias is required — proxy everything to gunicorn.

## Run

```bash
gunicorn --bind 127.0.0.1:8000 proj.wsgi:application
```

nginx: proxy `/` to `127.0.0.1:8000`, set `X-Forwarded-Proto https` (the
settings read `SECURE_PROXY_SSL_HEADER`), and terminate TLS. A systemd unit
keeps gunicorn running; pair with the usual `Restart=always`.

## Workers

Set `CELERY_BROKER_URL` to a real Redis and run alongside the web process:

```bash
celery -A proj worker -l info
```

Without a broker URL, jobs execute inline in the web process — acceptable for a
very early stage, not for production.

## After booting

- `python manage.py check --deploy` — act on the security warnings it prints.
- Hit `/accounts/login/` and complete a real Google sign-in.
- Create one Stripe price / Lemon Squeezy variant per tier and paste the IDs
  into `.env`, then exercise a checkout and confirm credits land.
- Confirm webhook delivery: `/billing/webhooks/lemonsqueezy/` or
  `/billing/webhooks/stripe/` (signature-verified; replay-safe).

## Ops commands

- `python manage.py validate_pending_uploads` — ffprobe-check pending media
- `python manage.py prune_job_scratch --older-than-days 7` — clean job workdirs
  (run under cron)
