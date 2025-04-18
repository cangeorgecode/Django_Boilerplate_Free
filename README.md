# Django + HTMX Boilerplate for SaaS | Free, setup in 15 mins 🚀🚀
### I raged and smashed 3 keyboards building this, so you don't have to 🎉 


&nbsp;


[![Pro](https://img.shields.io/badge/Pro-Boilerplate-pink)](https://vibecodesaas.com/) **Make boilerplates affordable again!** 👉 [Pro version - $29](https://vibecodesaas.com/)


&nbsp;


### Django Boilerplate: 
😎 Save Time (Skip 20+ hours of set up)  
😎 Save Money (Already saved $999)  
😎 Free forever  
😎 Unlimited projects  
😎 Instant Access  
😎 Lifetime update  

&nbsp;

## What you get right out of the box:
![Demo Video](https://raw.githubusercontent.com/cangeorgecode/djbp_demo_video/main/output.gif)


&nbsp;


## Features included  🔧

✅ Django, Tailwind + Kutty, HTMX  
✅ Django, Tailwind + DaisyUI, HTMX (in the "daisy" branch of this repo)  
✅ Wagtail CMS  
✅ User authentication (django-allauth)  
✅ Email verification  
✅ Landing page template optimized for conversion  
✅ Django admin panel  


&nbsp;


## Features coming to the Pro version 🚧

- Django Rest Framework
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
- Stripe (one-off & subscriptions) payment


&nbsp;


## Setup 🧑‍💻  
Run install.sh or manually install  


```
git clone https://github.com/cangeorgecode/Django_Boilerplate_Free <dir_name>
cd <dir_name>
source venv/bin/activate
pip install -r requirements.txt
python manage.py tailwind install
cd theme/static_src
npm i -D daisyui@latest
cd ../..
python manage.py tailwind build

python manage.py collectstatic --noinput
python manage.py migrate


# Check that everything is running
python manage.py runserver


# Create an .env file
touch .env


# Add your email host and password to .env
EMAIL_HOST_USER='add_your_email'
EMAIL_HOST_PASSWORD='add_your_password'

```


&nbsp;


## Cost breakdown 💰

- Hosting: $10/month (Get $60 credit on Linode with my [referral link](https://www.linode.com/lp/refer/?r=9ff0cd12e24c4e14bb041fd505242e605d1cc36d)
- Domain name: $60 (from Porkbun)
- Django Boilerplate: $0  


&nbsp;


## Contact me 📧

Hi, my name is George. 👋 I am a self-taught developer. I like coding and building things. Because I am working a 9 to 5, I need to be efficient with my time and money. I am sharing resources for free to help those who like to build things as well

- [X](https://x.com/joji_jiji)
- [Blog - No signup needed](https://joji.beehiiv.com/)
- [![Pro](https://img.shields.io/badge/Pro-Boilerplate-pink)](https://vibecodesaas.com/) [Make boilerplates affordable again!](https://vibecodesaas.com)

&nbsp;


P.S. Consider giving me a star ⭐ if you find this helpful, cheers! 🍻


