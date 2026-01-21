# Django Micro-SaaS Boilerplate 🚀
### A boilerplate that gives you a head start in monetization 🎉  

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

**BEFORE YOU BUY, READ THIS 🛑**  

1. **Please try the free version first**
2. Support will be limited, because I just become a father :D I will help out whenever I can.    
3. I have tested thoroughly but no guarantee it will work for you. Try the free version first.  
4. I am self-taught and I vibe coded half the project. Be prepared to get the worst of both worlds. I think I did ok in terms of security  
5. It's been tested in WSL2 and Ubuntu 24  

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
   git clone https://github.com/cangeorgecode/Django_Boilerplate_Free.git app
   cd app

2. **Create .env**  
    ```bash
    DEBUG = 'True' 
    SECRET_KEY = # You need to copy from settings.py
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

3. **Install nginx (Skip to step 4 if you are testing on local machine)**  
    I am using nginx in the host, not the docker nginx  

    ```bash
    sudo apt update  
    ```   

    ```bash
    sudo apt install nginx
    ```  

    **Configure /etc/nginx/sites-available/<app_name> as follows**  

    ```bash
    server {
        listen 80;
        server_name <domain_name>;

    location /static/ {
            alias /var/www/static/;
            expires 30d;
            access_log off;
        }

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```  

    ```bash
    sudo ln -s /etc/nginx/sites-available/<app_name> /etc/nginx/sites-enabled

    ```

    **Create host static dir**  
    ```bash
    sudo mkdir -p /var/www/static
    sudo chown -R www-data:www-data /var/www/static
    ```

    **Copy static files from container to host**  
    ```bash
    docker compose cp web:/app/staticfiles/. /var/www/static/
    ```

    **Reload nginx**
    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    ```


4. **Build the application**  
    ```bash
    docker compose build --no-cache
    ```

    **Run the application in foreground**
    ```bash
    docker compose up
    ```

    **Run application in background**
    ```bash
    docker compose up -d
    ```

    **Supports Tailwind hot reload in development**  
    ```bash
    docker compose up -d  
    docker compose run --rm web python manage.py tailwind dev
    ```

5. **Install certbot and get https for your app (Skip this step if you are testing on local machine)**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d <domain_name>
    ```  

6. **Open the app (locally)**
    Go to: http://localhost:8000   

7. **Troubleshooting commands**  
    Here are some places to take a look at if things don't work:  

    **Docker**  
    ```bash
    docker ps
    docker compose logs web  
    docker compose logs db
    ```  

    **Nginx**  
    ```bash
    sudo tail -20 /var/www/logs/nginx/error.log

    sudo systemctl status nginx
    ```


&nbsp;



## Free Hosting on Linode 💰

- I use Docker from the marketplace on Linode for this set up  
- Hosting: $10/month (Get $60 credit on Linode with my [referral link](https://www.linode.com/lp/refer/?r=9ff0cd12e24c4e14bb041fd505242e605d1cc36d)


&nbsp;


## Contact me 📧  

Hi, my name is George, a self-taught developer. My goal is to build a bunch of saas, make money, quit my job, become financially independent, so that I can spend time with my family. 

- [X](https://x.com/joji_jiji)

&nbsp;


P.S. If you like my project, a ⭐ would mean a lot to me, cheers! 🍻


