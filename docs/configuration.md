# Configuration

Everything is configured through environment variables in `.env`
(copy `.env.example` to get the full annotated template). Every feature
**degrades gracefully** when its variables are unset: providers hide from the
login page, billing disables, uploads stay on local disk, jobs run inline.

Rules:

- `load_dotenv` runs with `override=False`: a variable exported in your shell
  beats the `.env` value.
- Values are read at settings import; restart the dev server after changing
  `.env`.

## Core

| Variable       | Default                        | Notes                                             |
|----------------|--------------------------------|---------------------------------------------------|
| `BASE_URL`     | `http://localhost:8000`        | Public base URL, used in redirect URIs and links  |
| `SECRET_KEY`   | insecure dev fallback          | **Required before any deploy**: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DEBUG`        | `False`                        | `True` for local dev (disables SSL redirect)      |
| `ALLOWED_HOSTS`| localhost,127.0.0.1,...        | Comma-separated; include `testserver` for tests   |

## Database

`DB_ENGINE=sqlite` (default) uses `db.sqlite3` — no setup. For Postgres:

```
DB_ENGINE=postgres
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=prefer        # use 'require' in production
```

## Auth — Google (primary) and Meta/Facebook

Social-only auth (`SOCIALACCOUNT_ONLY=True`): there is no local
username/password signup, and Google supplies the verified email.

**Google**

1. Google Cloud Console -> create a project -> APIs & Services -> Credentials
   -> Create credentials -> **OAuth client ID** -> Web application.
2. Add authorized redirect URI: `<BASE_URL>/accounts/google/login/callback/`
3. Copy the client ID and secret:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

**Meta / Facebook** (optional)

1. Meta for Developers -> create app -> add the **Facebook Login** product.
2. Add a valid OAuth redirect URI: `<BASE_URL>/accounts/facebook/login/callback/`
3. Put the app in **Live** mode (in dev mode only admins/testers can sign in).
4. Copy the app ID and secret:

```
META_APP_ID=...
META_APP_SECRET=...
```

Credentials are wired as settings-based provider apps read from env — never add
the same provider as a SocialApp row in the Django admin (allauth raises
`MultipleObjectsReturned`). A provider with no credentials is automatically
hidden from the login page.

Clicking a provider button redirects straight to the provider's consent page
(`SOCIALACCOUNT_LOGIN_ON_GET=True`) — no intermediary page.

## Billing — Lemon Squeezy (primary) or Stripe

`billing/tiers.py` is the single source of truth for plans and pricing. Client
code never supplies prices; checkouts are created server-side and webhooks are
re-validated against these definitions.

- If the three `LEMONSQUEEZY_*` keys are all set, Lemon Squeezy is the gateway.
- Otherwise, if `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` are set, Stripe is
  the gateway.
- Otherwise billing is disabled (the pricing page says so).

```
# Lemon Squeezy (Merchant of Record — handles global tax/VAT)
LEMONSQUEEZY_API_KEY=...
LEMONSQUEEZY_WEBHOOK_SECRET=...
LEMONSQUEEZY_STORE_ID=...
LEMONSQUEEZY_VARIANT_STARTER=...
LEMONSQUEEZY_VARIANT_GROWTH=...
LEMONSQUEEZY_VARIANT_SCALE=...
LEMONSQUEEZY_VARIANT_TOPUP_5=...

# Stripe
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
STRIPE_PRICE_STARTER=...
STRIPE_PRICE_GROWTH=...
STRIPE_PRICE_SCALE=...
STRIPE_PRICE_TOPUP_5=...
```

Create one price (Stripe) or variant (Lemon Squeezy) per tier, then paste its ID
into the matching variable. The tier slugs and prices live in
`billing/tiers.py` — change the product there, not in templates.

Webhook endpoints (signature-verified, replay-safe):

- `/billing/webhooks/lemonsqueezy/`
- `/billing/webhooks/stripe/`

`STRIPE_WEBHOOK_SECRET` must be set or the Stripe webhook refuses to grant
credits.

## Storage — Cloudflare R2

S3-compatible object storage with local-disk fallback:

```
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_PUBLIC_URL=           # optional custom domain, e.g. https://media.example.com
MAX_STORAGE_BYTES_PER_USER=2147483648   # per-user quota, default 2 GB
```

Until the first three are set, uploads land in local `FileSystemStorage`
(media root). R2 specifics handled for you: region `auto`, path-style
addressing, no ACLs. Transfers use presigned URLs scoped to the exact object
key, content type and a short TTL. The upload flow is two-step
(`/uploads/initiate/` then a presigned PUT or direct POST to
`/uploads/complete/`), followed by `/uploads/assets/<id>/validate/` which runs
ffprobe validation. If you use R2, allow the app's origin in the bucket's CORS
settings or browser uploads will fail. Rejected files are deleted from storage
automatically and their bytes reclaimed from the quota.

## Email

Gmail SMTP is pre-wired; in `DEBUG` the console backend is used so nothing is
ever sent during development.

```
EMAIL_HOST_USER=...          # a Gmail address
EMAIL_HOST_PASSWORD=...      # an app password, not the account password
DEFAULT_FROM_EMAIL=no-reply@example.com
```

## Jobs — Celery

```
CELERY_BROKER_URL=redis://localhost:6379/0
```

Leave it empty in dev: tasks run inline (eager) so the pipeline works without
Redis. In production, run workers:

```bash
celery -A proj worker -l info
```

## Video pipeline services

```
DEEPGRAM_API_KEY=...        # transcription (nova-3; zh-HK + en)
ELEVENLABS_API_KEY=...      # voiceover
ELEVENLABS_VOICE_ID=...     # which voice
DEEPSEEK_API_KEY=...        # agent stage: caption/cut decisions
DEEPSEEK_MODEL=deepseek-chat
```

ffmpeg/ffprobe must be on PATH (or point `FFMPEG_BINARY` / `FFPROBE_BINARY` at
the binaries). Output is 1080x1920 (9:16) by default; override with
`OUTPUT_VIDEO_WIDTH` / `OUTPUT_VIDEO_HEIGHT`.

## Operations commands

- `python manage.py validate_pending_uploads` — ffprobe-check pending media
- `python manage.py prune_job_scratch --older-than-days 7` — clean finished job
  workdirs
