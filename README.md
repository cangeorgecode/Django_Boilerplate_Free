# Django Boilerplate

I built 4 apps in 2 weeks with this. Build a reliable MVP in 2 weeks

## Installation

### Download the files

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

## Please note

Debug is set to True and allowed hosts haven't been set in the settings.py file.

## API, secret keys in the .env file

You will need:

# For django-allauth, I have set every new user needs to confirm their email address
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD

## Tech stack

- Django
- Tailwind
- Kutty
- HTMX

## Features & Benefits

- Authentication included
  - Login, logout, registration
  - Password reset
  - Email verification
  - (Optional) Login with social media
- Landing page template optimized for conversion
- Wagtail CMS management 
- Free to use
- Lifetime update
- Unlimited projects

## Need help? Find me on X or raise an issue here on Github

- My X: https://x.com/joji_jiji
