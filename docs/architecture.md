# Architecture

djbp_free is a Django monolith with a clear seam for background work. One code
path runs the web app; the same code runs a Celery worker (or inline, in dev).

## Apps

| App        | Responsibility                                                  |
|------------|-----------------------------------------------------------------|
| `proj`     | Settings, URLs, Celery app config                               |
| `core`     | Base templates, home/dashboard/terms/privacy views              |
| `accounts` | Login page + allauth template overrides                         |
| `billing`  | Tiers, checkouts, webhooks, credit ledger (`CreditAccount`, `CreditTransaction`, `Subscription`, `PaymentEvent`) |
| `uploads`  | User media intake: validation, quarantine, presigned R2 uploads |
| `jobs`     | Pipeline jobs: state machine, stages, progress, cost reports    |
| `theme`    | django-tailwind app; Tailwind v4 + daisyUI sources              |

## Auth flow

- `SOCIALACCOUNT_ONLY=True`: only social login exists. `/accounts/login/`
  renders the custom login template; signup/password-reset URLs are not
  registered.
- Provider credentials come only from env (`SOCIALACCOUNT_PROVIDERS` APP
  dicts) — no `SocialApp` rows in the DB, ever. A provider without creds is
  filtered out of `{% get_providers %}` and its button disappears.
- `SOCIALACCOUNT_LOGIN_ON_GET=True`: the provider login URL (e.g.
  `/accounts/google/login/`) is a pure redirect to the provider's consent page.
- After the OAuth callback, allauth logs the user in and redirects to
  `LOGIN_REDIRECT_URL`.

## Billing + credits

- `billing/tiers.py` is the single source of truth: tier slugs, prices, credit
  amounts, top-up packs, and which gateway is configured.
- Gateways: Lemon Squeezy (Merchant of Record) when configured, else Stripe,
  else nothing.
- Checkout creation resolves price/variant IDs server-side from env. The client
  only sends a tier slug.
- Webhooks (`/billing/webhooks/<gateway>/`) verify the signature **before**
  parsing the payload, re-validate amounts against server-side truth, and grant
  credits idempotently (replay-safe).
- The credit ledger is atomic: grants/spends/refunds happen inside
  `transaction.atomic()` with unique idempotency references.

## Job pipeline

```
upload (browser -> presigned R2 PUT)
  -> job (state machine: queued -> transcribe -> agent -> render -> assemble)
  -> transcribe  (Deepgram nova-3; local faster-whisper as offline fallback)
  -> agent       (DeepSeek/Hermes: script -> caption cues / cut points)
  -> TTS         (ElevenLabs)
  -> render      (ffmpeg assembly, 1080x1920)
  -> deliver     (presigned R2 download URL)
```

- Jobs run through Celery when `CELERY_BROKER_URL` is set; otherwise inline
  (dev).
- Untrusted media is quarantined, ffprobe-validated, and processed with
  resource limits; transcribed/script content is always treated as data, never
  as instructions.
- Each job records a `cost_breakdown` (transcription, TTS, LLM, storage) to
  feed the credit-pricing model.

## Storage

- `STORAGES['default']` is `S3Storage` (R2) when `R2_ACCESS_KEY_ID` /
  `R2_SECRET_ACCESS_KEY` / `R2_BUCKET_NAME` are all set, else
  `FileSystemStorage`.
- All R2 transfers go through presigned URLs scoped to the exact object key,
  content type, and short TTL — the bucket itself is never public.
- `STORAGES['staticfiles']` is `CompressedManifestStaticFilesStorage`
  (WhiteNoise serves static in production; run `collectstatic` on deploy).

## Security posture

- Social auth only; emails verified by the provider.
- Server-side pricing; webhook signature verification before parsing;
  idempotent credit grants.
- Upload allowlists (extension + content type + size), UUID-renamed keys,
  quarantine until validated, presigned URL scoping.
- Production settings block (`DEBUG=False`): HSTS, secure cookies, SSL
  redirect, `X-Frame-Options: DENY`, nosniff, referrer policy.
- Explicit field whitelists on forms; no `fields='__all__'`; user content is
  never rendered unescaped.

## Where to extend

- New pipeline stage: add a step in the job state machine (`jobs/`) and a
  service module; register its cost in `cost_breakdown`.
- New product tier: edit `billing/tiers.py` and create the matching
  price/variant in your gateway, then set the env ID.
- New page: add a view in `core/` (or a new app), a URL, and a template
  extending `core/base.html`.
- New Tailwind classes: edit templates, then `npm run build` in
  `theme/static_src` (or keep `npm run dev` running).
