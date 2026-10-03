from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')




# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Generate one with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-dev-only-not-for-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,[::1]').split(',')

SITE_ID = 1

# Production overrides (will be set on Linode)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tailwind',
    'theme',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'core', 
    'accounts',
    'billing',
    'uploads',
    'jobs',
    "django_htmx",
    
]

if DEBUG:
    # Add django_browser_reload only in DEBUG mode
    INSTALLED_APPS += ["django_browser_reload"]

TAILWIND_APP_NAME = 'theme'

INTERNAL_IPS = [
    "127.0.0.1",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

if DEBUG:
    # Add django_browser_reload middleware only in DEBUG mode
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_ONLY = True
# Clicking a provider login link redirects STRAIGHT to Google/Meta's sign-in page
# (no intermediary /accounts/<provider>/login/ confirmation page).
SOCIALACCOUNT_LOGIN_ON_GET = True

# Google-only auth: Google supplies the (already verified) email.
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # required by SOCIALACCOUNT_ONLY (default already resolves to 'none')
ACCOUNT_USER_MODEL_USERNAME_FIELD = None # no usernames needed
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*']

# Prevent any local signup/login forms from appearing or working
ACCOUNT_SIGNUP_FORM_CLASS = None
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

# Social providers: Google + Meta (Facebook). Credentials come ONLY from env,
# so the boilerplate ships with zero secrets. A provider without creds is
# automatically hidden from the login page (allauth filters providers that
# have no configured app). Never ALSO add the same provider as a SocialApp
# in the admin DB — allauth raises MultipleObjectsReturned.
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        # Graph API version override (default: v19.0):
        # 'VERSION': 'v21.0',
    },
}

_google_client_id = os.getenv('GOOGLE_CLIENT_ID')
_google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
if _google_client_id and _google_client_secret:
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': _google_client_id,
        'secret': _google_client_secret,
    }

_meta_app_id = os.getenv('META_APP_ID')
_meta_app_secret = os.getenv('META_APP_SECRET')
if _meta_app_id and _meta_app_secret:
    SOCIALACCOUNT_PROVIDERS['facebook']['APP'] = {
        'client_id': _meta_app_id,
        'secret': _meta_app_secret,
    }

# Where to redirect after successful login
LOGIN_REDIRECT_URL = '/'

# Optional: redirect after logout
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

ROOT_URLCONF = 'proj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'accounts/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'proj.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Default: SQLite (zero-config, fine for the vast majority of small apps).
# To use Postgres instead, set DB_ENGINE=postgres in your .env and fill the DB_* vars.
if os.getenv('DB_ENGINE', 'sqlite') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': os.getenv('DB_SSLMODE', 'prefer'),  # 'prefer' locally, 'require' in prod
            },
            'CONN_MAX_AGE': 60,
            'DISABLE_SERVER_SIDE_CURSORS': False,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media storage: Cloudflare R2 when configured, local disk otherwise (dev).
# R2 is S3-compatible but needs region 'auto', path-style addressing, and
# NO ACLs (R2 rejects ACL headers — AWS_DEFAULT_ACL must stay None).
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', '')
R2_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL', '')
R2_PUBLIC_URL = os.getenv('R2_PUBLIC_URL', '')  # optional custom domain, e.g. https://media.example.com

if R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME:
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3.S3Storage'}
    AWS_ACCESS_KEY_ID = R2_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = R2_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = R2_BUCKET_NAME
    AWS_S3_ENDPOINT_URL = R2_ENDPOINT_URL
    AWS_S3_REGION_NAME = 'auto'
    AWS_S3_ADDRESSING_STYLE = 'path'
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None  # R2 does not support ACLs
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 3600
else:
    STORAGES['default'] = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}

# Per-user storage quota (bytes). Enforced at upload initiate AND complete.
MAX_STORAGE_BYTES_PER_USER = int(os.getenv('MAX_STORAGE_BYTES_PER_USER', str(2 * 1024**3)))


# Email — Gmail SMTP when creds are set; console backend in dev so nothing
# is ever sent accidentally during development.
if DEBUG:
    EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
else:
    EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@localhost')


# Job pipeline — work dir for intermediate artifacts (scratch, cleaned per job)
JOB_WORK_DIR = os.path.join(BASE_DIR, 'media', 'jobs')

# Celery (Redis broker; unset = tasks run inline for local dev)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', '')
CELERY_TASK_TIME_LIMIT = int(os.getenv('CELERY_TASK_TIME_LIMIT', '1800'))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '1500'))

# Pipeline API services (all optional; each stage degrades or fails cleanly)
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', '')
DEEPGRAM_MODEL = os.getenv('DEEPGRAM_MODEL', 'nova-3')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', '')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

# Video assembly
FFMPEG_BINARY = os.getenv('FFMPEG_BINARY', 'ffmpeg')
FFPROBE_BINARY = os.getenv('FFPROBE_BINARY', 'ffprobe')
OUTPUT_VIDEO_WIDTH = int(os.getenv('OUTPUT_VIDEO_WIDTH', '1080'))
OUTPUT_VIDEO_HEIGHT = int(os.getenv('OUTPUT_VIDEO_HEIGHT', '1920'))


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'theme/static/'),
]
MEDIA_ROOT =  os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

# Stripe (secondary gateway; Lemon Squeezy is the primary MoR)
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PRICE_ID = os.getenv('STRIPE_PRICE_ID', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Lemon Squeezy (primary, Merchant of Record)
LEMONSQUEEZY_API_KEY = os.getenv('LEMONSQUEEZY_API_KEY', '')
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv('LEMONSQUEEZY_WEBHOOK_SECRET', '')
LEMONSQUEEZY_STORE_ID = os.getenv('LEMONSQUEEZY_STORE_ID', '')

# "For no one can lay a foundation other than that which is laid, which is Jesus Christ - 1 Corinthians 3:11"