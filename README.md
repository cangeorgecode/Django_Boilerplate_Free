# Django Micro-SaaS Boilerplate 🚀
### How you can make money by selling digital products 🎉  

This free version supports Stripe single payment. You can create a product, plug in the API keys and start selling.  

&nbsp;

### Here's how I'd make money:  

1. Find a profitable idea - does it provide 'value' for others:  
    - Make or save money  
    - Save time  
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


&nbsp;


### Subscription-based boilerplate for recurring revenue 

Subscription-based boilerplate ($99, one time purchase) available here → (Link to be added)  

**Do NOT buy until you have tried the free version and you are ok with:**  

1. I have just become a dad and life is hectic. I have limited time to support, but I will support whenever I can  
2. Docker is new to me, I have tested it quite thoroughly, but no guarantee it works on your end. I am confident in other parts of the code  
3. I am self-taught and I vibe coded half the project. Be prepared to get the worst of both worlds. I think I did ok in terms of security  


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

3. **Install nginx (when you deploy)**
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


4. **Start the application**  
    ```bash
    docker compose up --build
    ```

5. **Install certbot and get https for your app**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d <domain_name>
    ```  

6. **Open the app (locally)**
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


