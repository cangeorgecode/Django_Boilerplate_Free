# Django Micro-SaaS Boilerplate 🚀
### How you can make money with this 🎉  

This free version supports Stripe single payment, meaning you can sell a digital product. Here's how I am using this to make money:  

1. Build a product that provides "value":
    - Make or save money
    - Save time
    - Mitigate risks
    - Raise social status

2. Market on X, LinkedIn, Reddit, SEO. Better yet, automate this

3. Repeat and build a portfolio of micro-saas → financial independence


&nbsp;



## Subscription-based SaaS boilerplate

If you are looking for a subscription-based saas boilerplate, I am building one. You can join the waitlist here → LINK (to be added)


&nbsp;


## The Stack (No Javascript)

✅ Django  
✅ Tailwind + DaisyUI  
✅ HTMX  
✅ Stripe (one off payment)  
✅ Django-allauth  
✅ Postgresql  
✅ Docker  
✅ Landing page optimized for conversion    


&nbsp;


## Installation

This project is designed to run with **Docker**

### Prerequisites

- **Docker** (with Docker Compose) installed  
  - Windows / macOS: Download from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
  - Linux: Follow your distro guide (e.g. `sudo apt install docker.io docker-compose` on Ubuntu)

**Note:** You do **not** need to install Python, PostgreSQL, Node.js, or any other tools locally — Docker handles everything.

&nbsp;


### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/your-saas-boilerplate.git
   cd your-saas-boilerplate

2. **Create and configure the environment file**  
    ```bash
    DEBUG = 'True' 
    SECRET_KEY = 
    ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,[::1]

    # Postgres
    DB_HOST = ''
    DB_NAME = ''
    DB_USER = ''
    DB_PASSWORD = ''
    DB_SSLMODE = 'prefer' # ← Change to require in prod 

    # Stripe
    STRIPE_PUBLISHABLE_KEY = ''
    STRIPE_SECRET_KEY = ''
    STRIPE_WEBHOOK_SECRET = ''
    STRIPE_PRODUCT_ID = ''
    STRIPE_PRICE_ID = ''

    # For production, uncomment
    # DATABASE_URL=postgres://user:pass@host:5432/dbname
    # DJANGO_SETTINGS_MODULE=proj.settings.production
    ```

3. **Start the application**  
    ```bash
    docker compose up --build
    ```

4. **Apply database migrations & create superuser**
    ```bash
    docker compose exec web python manage.py migrate
    docker compose exec web python manage.py createsuperuser
    ```  

5. **Open the app**
    Go to: http://localhost:8000  


&nbsp;



## Free Hosting on Linode 💰

- Hosting: $10/month (Get $60 credit on Linode with my [referral link](https://www.linode.com/lp/refer/?r=9ff0cd12e24c4e14bb041fd505242e605d1cc36d)


&nbsp;


## Contact me 📧  

Hi, my name is George, a self-taught developer. My goal is to build a bunch of saas, make money, quit my job, become financially independent, so that I can spend time with my family. 

- [X](https://x.com/joji_jiji)

&nbsp;


P.S. If you like my project, a ⭐ would mean a lot to me, cheers! 🍻


