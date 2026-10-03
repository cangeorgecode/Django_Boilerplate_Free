# djbp_free Upgrade TODO

## App shell (existing)

[x] Auth: add Meta (Facebook) login alongside Google — BOTH providers fully configured
   - Fix blocker: Google creds currently configured NOWHERE (no APP dict, no .env, 0 SocialApp rows) — clicking the Google button crashes with SocialApp.DoesNotExist
   - Add 'allauth.socialaccount.providers.facebook' to INSTALLED_APPS
   - Add 'facebook' provider to SOCIALACCOUNT_PROVIDERS (scope: email, public_profile; default METHOD oauth2; optional VERSION override — default Graph API v19.0)
   - Standardize credentials: settings-based APP dict read from env for BOTH providers. Never mix a settings APP and a DB SocialApp for the same provider (allauth raises MultipleObjectsReturned)
   - Create .env with META_APP_ID, META_APP_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET (edit via patch only)
   - Login template: add Facebook button (Google button is hardcoded today)
   - Set SOCIALACCOUNT_EMAIL_VERIFICATION='none' explicitly (default already resolves to none under SOCIALACCOUNT_ONLY)
   - Fix login.html Terms/Privacy placeholder '#' links
   - Run manage.py check (expect zero issues)
   [human] Google Cloud console: create OAuth 2.0 client, paste GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET
   [human] Google Cloud console: add authorized redirect URI <domain>/accounts/google/login/callback/
   [human] Meta developer console: create app, enable Facebook Login product, set valid OAuth redirect URI <domain>/accounts/facebook/login/callback/, set app mode Live (dev mode only lets admins/testers log in), paste META_APP_ID + META_APP_SECRET
   [later] Style socialaccount templates (default allauth ones are unstyled; only triggers on email-collision flow) — defer

[x] Payments: Lemon Squeezy PRIMARY (MoR — handles global tax/VAT remittance), Stripe secondary
   - Lemon Squeezy checkout + signed webhook (recipe: ~/.hermes/skills/software-development/django-saas-boilerplate/references/lemon-squeezy.md)
   - Monthly tiers + top-up packs created as LS products/variants
   - .env: LEMONSQUEEZY_API_KEY, LEMONSQUEEZY_WEBHOOK_SECRET, LEMONSQUEEZY_STORE_ID, tier variant IDs
   - Refactor current one-off Stripe Checkout into a shared billing module supporting both gateways (LS first)

[x] Billing: credits-based subscriptions + top-ups (design LOCKED)
   - Tiers: $19/mo = 10 credits, $45/mo = 20 credits (decoy, pushes to top), $49/mo = 30 credits (target — badge "Best Value", pre-selected)
   - Top-up pack: $9 = 5 credits (confirmed)
   - 1 credit = 1 standard video (confirmed)
   - Metering primitive: own credits ledger (CreditBalance/CreditTransaction) + LS/Stripe top-up checkouts (decision #1 locked)
   - Add credits deduction on usage

[x] Media: Cloudflare R2 for user uploads, readable from the main app on the other VPS
   - Add 'default' storage backend (django-storages + boto3 S3Storage), keyed off R2_ACCESS_KEY_ID so dev falls back to local FileSystemStorage
   - R2 specifics: AWS_S3_REGION_NAME='auto', AWS_S3_ADDRESSING_STYLE='path', AWS_S3_ENDPOINT_URL from env
   - Create R2 bucket + API token; keys into .env
   - Access model: presigned URLs everywhere (browser PUT upload, worker GET, user GET download) — no custom domain needed initially

[x] Email: admin function to send emails to users (support replies only — no bulk sends)
   - Admin compose form + action: send to selected users or all users
   - Route through existing Gmail SMTP (EMAIL_HOST_USER/EMAIL_HOST_PASSWORD); DEFAULT_FROM_EMAIL = support address

## Security hardening (app-wide)

[x] Untrusted file uploads: extension + content-type allowlist, max size caps, filename sanitization (uuid rename — never use user-supplied filenames), ffprobe pre-flight validation before processing, quarantine uploads until validated, presigned URLs scoped to bucket prefix + content-type + max size + short TTL, never execute anything derived from uploads
[x] User input sanitization: explicit field whitelists on every form/serializer (never fields='__all__'), server-side validation of all inputs, audit templates for |safe/mark_safe/raw HTML, never render user content unescaped
[x] Hidden inputs / client-tamper protection: never trust client-supplied values (prices, amounts, variant/price IDs, credit counts) — resolve server-side from DB/env; re-validate every payment webhook against server-side truth before granting access/credits; idempotent credit grants (replay-safe); audit csrf_exempt usage (only signature-verified webhooks may use it)

## AaaS runtime (video pipeline engine)

Target blueprint (solo scale, ~1000 MAU per product):
- ONE VPS per product: Django + Postgres/SQLite + Redis + Celery workers + one Docker container per running agent job (isolation)
- R2 = media data plane; VPS disk = temporary scratch only, cleaned per job
- Scale-out path: second worker VPS pointed at the same Redis — config change, no rewrite
- File flow: browser -> presigned direct upload to R2 (bytes bypass app server) -> worker pulls to scratch -> processes -> writes output to R2 -> user gets presigned download link

[x] Job queue: Celery + Redis; web app enqueues, background workers process (same VPS for now, CPU-limited so site never freezes). Code done — Redis broker deploy on the VPS pending (CELERY_BROKER_URL); without a broker, jobs run inline (eager) so dev works
[x] Job model + state machine: status, stage (queued -> transcribe -> agent -> render -> assemble -> done/failed), progress %, logs, retry, cancel, timeout
[x] Job progress to UI: SSE or HTMX polling — chose polling (JS fetch every 2.5s on the job detail page)
[x] Pipeline stages as reusable services: upload footage + script -> ElevenLabs TTS -> transcribe -> [agent stage, optional per product] -> render/cut -> deliver. faceless-explainer v1 = user-uploaded footage + user-written script, NO Runware video gen
[] Transcription stage: LOCKED — Deepgram nova-3 batch API (~$0.0043/min pay-as-you-go, zh-HK + en; proven accurate on Cantonese in canto_transcriber_web). A 5-min video costs ~$0.02. Local faster-whisper large-v3 stays as offline fallback only. NEVER ship small/base (broken/hallucinate on Cantonese). NOTE: DEEPGRAM_API_KEY already exists in the local shell env — the pipeline picks it up automatically
   [human] Deepgram console: confirm/create API key, paste DEEPGRAM_API_KEY into .env for the VPS
[x] Repackage local video skills as platform services: env-driven paths, no interactive steps, no hardcoded ~/Projects paths. Deepgram/DeepSeek/ElevenLabs/ffmpeg services built. HyperFrames port deferred to a future pipeline (v1 uses ffmpeg assembly)
[] Agent stage (dr-mak style): DeepSeek + Hermes read the uploaded SCRIPT, decide how to break it into caption cues (timed to footage/VO); dr-mak variant reads the transcript to pick cut points. Runs in per-job Docker container, allowlisted tools, no secrets. Verify headless Hermes deployment against the Hermes docs Security page before building
   - DONE: script -> caption cues via DeepSeek with deterministic fallback + sanity check; injection treated as data
   - REMAINS: dr-mak transcript-cut variant; per-job Docker isolation; headless Hermes verification (deployment)
[x] Upload flow: presigned direct-to-R2 multipart uploads; worker scratch cleanup; presigned output download; per-user quota + per-job object lifecycle cleanup
   - DONE: presigned PUT/GET (scoped key + content-type + TTL), scratch prune command (prune_job_scratch), ownership-gated download
   - DONE: upload UI (/uploads/ — two-step initiate -> PUT/POST -> complete -> ffprobe validate, asset library, quota bar) + per-user storage quota (MAX_STORAGE_BYTES_PER_USER, enforced at initiate AND complete, rejected files auto-deleted)
   - [human] Cloudflare: add CORS rule to the R2 bucket allowing the app origin — browser presigned PUTs fail without it (verified)
[x] Cost metering design: credit mapping for worker CPU-min, whisper, LLM tokens, ElevenLabs TTS, R2 storage (no image/video gen in v1); pre-job cost estimate shown before checkout + per-job cost report. Metering primitive RESOLVED: own credits ledger + LS/Stripe top-up checkouts. Flat 1 credit/job + per-job cost_breakdown JSON recorded
[x] Security: sandbox ffmpeg/ffprobe on untrusted media (CPU/mem/time limits, no network); treat transcribed content as data, never instructions (prompt injection); tenant isolation between concurrent jobs. Code-level done (timeouts, injection-as-data, ownership checks); OS-level sandbox (rlimits, no network) applies at worker deploy
[x] Third-party API reliability: idempotency + retry/backoff (ElevenLabs, Runware, etc.); cache intermediate artifacts so a job resumes after an API outage without re-billing expensive stages. Done: retry_call wrapper, per-stage artifact caching in job workdir, billing event idempotency
[x] ComfyUI: RESOLVED — no ComfyUI anywhere. Runware API only if a future pipeline needs generation; faceless-explainer v1 needs none (users upload own footage + script)
[x] Scope: ship ONE pipeline end-to-end first — faceless-explainer (confirmed), then add more agents/pipelines. Pipeline skeleton complete: credits -> job -> stages -> render -> deliver
