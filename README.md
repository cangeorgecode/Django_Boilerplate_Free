# Build a reliable MVP in 2 weeks

![Demo Video](https://raw.githubusercontent.com/cangeorgecode/djbp_demo_video/main/output.gif)

## Why Django?
Django may not be the fastest, but it's reliable, secure and modular. It makes for a perfect backend to build an MVP quickly. 


## Features

- Django, Tailwind + Kutty, HTMX
- Wagtail CMS
- User authentication (django-allauth)
- Email verification
- Landing page template optimized for conversion
- Django admin panel
- Stripe | Pro version only

## Features to add

- Django Rest Framework for api
- Social media login
- Posthog analytics
- User management dashboard
- Email template
- Sentry logging
- Multi-tenancy
- Deployment script
- Redis, Celery integration
- Docker setup
- CSV import/export

## Setup

```
git clone https://github.com/cangeorgecode/Django_Boilerplate_Free <dir_name>
cd <dir_name>
source venv/bin/activate
pip install -r requirements.txt
python manage.py tailwind install
npm i kutty --save
python manage.py tailwind start

# Open another terminal or Ctrl + C
python manage.py collectstatic # Type yes if prompted
python manage.py migrate

# Check that everything is running
python manage.py runserver

```

### Please note

Debug is set to True and allowed hosts haven't been set in the settings.py file.



### API, secret keys in the .env file

For django-allauth, I have set every new user needs to confirm their email address
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD

## Contact me

- My X: https://x.com/joji_jiji
