# Django Micro-SaaS Boilerplate 🚀
### A boilerplate that gives you a head start in monetization 🎉  

## This build (AaaS runtime)

Added on top of the base boilerplate:
- Auth: Google + Meta (Facebook) via allauth, env-driven credentials, no DB SocialApps
- Billing: Lemon Squeezy (primary, Merchant of Record) + Stripe (secondary); subscriptions, top-ups, signed webhooks, idempotent event processing
- Credits: own ledger (CreditAccount/CreditTransaction) — 1 credit = 1 video; grants, spends, refunds all atomic + idempotent
- Media: Cloudflare R2 (S3-compatible, region auto, path style, no ACLs) with presigned direct uploads/downloads; local-disk fallback in dev; ffprobe validation + quarantine
- Jobs: Celery pipeline (transcribe -> caption plan -> TTS -> ffmpeg assemble -> 9:16 mp4), progress polling, per-job cost report, credit refund on pre-execution failure
- Admin: staff email-to-users page (selected or all)
- Security: upload allowlists/size caps/UUID keys, server-side pricing resolution, webhook signature verification before parsing, HSTS/nosniff/referrer-policy/frame-deny in prod

## Documentation

- [Getting Started](docs/getting-started.md) — what this is, prerequisites, install, run
- [Configuration](docs/configuration.md) — every environment variable and how to get the real credentials
- [Architecture](docs/architecture.md) — how the apps, auth, billing and pipeline fit together
- [Deployment](docs/deployment.md) — production checklist

### Environment variables (all optional — features degrade gracefully without them)

See [.env.example](.env.example) for the full annotated template. Groups:
- Auth: GOOGLE_CLIENT_ID/SECRET, META_APP_ID/SECRET (provider hidden from login until set)
- Billing: LEMONSQUEEZY_API_KEY/WEBHOOK_SECRET/STORE_ID + LEMONSQUEEZY_VARIANT_{STARTER,GROWTH,SCALE,TOPUP_5}; STRIPE_SECRET_KEY/WEBHOOK_SECRET + STRIPE_PRICE_{...}
- Media: R2_ACCESS_KEY_ID/SECRET_ACCESS_KEY/BUCKET_NAME/ENDPOINT_URL (until set, uploads stay on local disk)
- Email: EMAIL_HOST_USER/PASSWORD, DEFAULT_FROM_EMAIL (console backend in DEBUG)
- Pipeline: DEEPGRAM_API_KEY, ELEVENLABS_API_KEY/VOICE_ID, DEEPSEEK_API_KEY/MODEL
- Worker: CELERY_BROKER_URL (Redis). Empty = jobs run inline (dev only).

### Run

    python manage.py tailwind build   # after npm ci in theme/static_src
    python manage.py migrate
    python manage.py test             # 36 tests
    python manage.py runserver 8001

### Ops

- validate_pending_uploads — ffprobe-check pending media
- prune_job_scratch --older-than-days 7 — clean finished job workdirs
- Webhooks (signature-verified, replay-safe): /billing/webhooks/lemonsqueezy/ and /billing/webhooks/stripe/


## Free 🆚 Premium


| Free                    | [Premium](https://vibecodesaas.com)|
|-------------------------|------------------------------------|
| Django                  | Django                             |
| Tailwind + DaisyUI      | Tailwind + DaisyUI                 |
| HTMX                    | HTMX                               |
| Stripe (one-off payment)| Stripe (recurring)                 |
| Django-allauth          | Django-allauth                     |
| Postgresql              | Postgresql                         |
| Docker                  | Docker                             |

&nbsp;

### Get the premium version today 🤑

Start charging your users today → [Premium SaaS Boilerplate, ~~$199~~ $99 Launch Discount](https://vibecodesaas.com)  

**🛑 BEFORE YOU BUY, READ THIS 🛑**  

1. **Please try the free version first**
2. Support will be limited, because I just become a father :D but will help out whenever I can.    
3. Tested thoroughly but no guarantee it will work for you. 
4. Code is unprofessional  
5. It's been tested in WSL2 and Ubuntu 24  
6. This repo will be as far as documentation goes
7. You can expect the same results with the premium version

&nbsp;

### Monetization Playbook 📖

1. Find a profitable idea - does it provide 'value' for others:  
    - Make or save money  
    - Save time, less work  
    - Overcome technical barrier  
    - More followers  
    - Go viral - more views, more likes, more shares, more save  
    - Increase exposure  

2. Validate idea in 2 weeks  
    - Build a free MVP in no more than 5 days  
    - Share on Reddit  
    - Collect feedbacks, reviews  
    - Put up a landing page using reviews as testimonials, include premium version  
    - Post on X, LinkedIn  

3. Marketing strategy. I tried SEO, ads, organic posts, newsletter but here's the marketing funnel I settled on:  
    - Post lessons learned in a very specific niche. People appreciate it when you give them something without expecting anything in return  
    - Ask people to leave a comment  
    - Trigger auto DM. You can use Manychat but I am building my own. This turns cold traffic to warm leads  
    - Make your offer privately in DM  

4. Storytelling to build trust and make sales even if you are a bad writer:  
    - Hook - be specific (niche audience, results) and quantifable (revenue, churn, timeframe)  
    - Backstory - share the struggle or problem that prompted you to look for a solution - people can relate when you have been in their shoe  
    - Breakthru - sudden shift in mindset, discovered something new  
    - Takeaway - share what you have learn, give actionable step by step guide  
    - CTA - ask people to comment (for marketing funnel) or ask people to share and save (for algo)  

5. My favourite hooks collection that can't be found on Google:  
    - "Is it possible to..."  
    - "Can I..."  
    - "It took me X months, but I finally figured out how to..."  
    - "How I..."  
    - "I failed..."  


&nbsp;


## Installation ⚙️

This project runs locally with Python + PostgreSQL. No Docker required.

### Prerequisites

- Python 3.13+
- Node.js 18+ (only needed to build the Tailwind/DaisyUI CSS)

### Step-by-Step Setup

1. **Create a virtualenv and install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create `.env`**
   ```bash
   DEBUG='True'
   SECRET_KEY=your-generated-secret-key
   ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
   BASE_URL=http://localhost:8000

   # Database: SQLite is the default and needs nothing.
   # To use Postgres instead, uncomment:
   # DB_ENGINE=postgres
   # DB_HOST=localhost
   # DB_NAME=your_db
   # DB_USER=your_user
   # DB_PASSWORD=your_password
   # DB_SSLMODE=prefer

   # Stripe
   STRIPE_PUBLISHABLE_KEY=
   STRIPE_SECRET_KEY=
   STRIPE_WEBHOOK_SECRET=
   STRIPE_PRICE_ID=
   ```

   Generate a secret key with:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Build the frontend CSS (Tailwind + DaisyUI)**
   ```bash
   cd theme/static_src
   npm install
   npm run build        # one-time production build
   # npm run dev        # watch mode while developing
   cd ../..
   ```

4. **Migrate and run**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py runserver
   ```

5. **Open the app** → http://localhost:8000


&nbsp;


## Deployment 💰

Deploy anywhere that runs Python (Linode, DigitalOcean, etc.). SQLite is fine on a single server for low-to-moderate traffic; switch to Postgres (`DB_ENGINE=postgres`) when you need multiple workers/servers or higher write volume.

1. Build the CSS (step 3 above) and run `python manage.py collectstatic --noinput`.
2. Serve with gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:8000 proj.wsgi:application
   ```
3. Put nginx in front — proxy `/` to `127.0.0.1:8000` and serve `/static/` from the `staticfiles/` directory.
4. Set `DEBUG='False'`, a real `SECRET_KEY`, and your domain in `ALLOWED_HOSTS`.


&nbsp;


## Contact me 📧  

Hi, my name is George, a self-taught developer. My goal is to build a bunch of saas, make money, quit my job, become financially independent, so that I can spend time with my family. 

- [X](https://x.com/joji_jiji)

&nbsp;


P.S. If you like my project, a ⭐ would mean a lot to me, cheers! 🍻
