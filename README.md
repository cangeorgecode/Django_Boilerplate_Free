# Django Micro-SaaS Boilerplate 🚀
### Building a portfolio of micro saas, so that I can spend time with family while still be able to provide financially 🎉  

Hi, I'm George — a self-taught developer with a dream. Like many of us, I got tired of the soul-sucking 9-5 grind stealing time from my family.  

So, I started building a portfolio of micro-SaaS to generate passive-ish income. The more I ship, the closer I get to financial freedom and more family moments.  

This boilerplate lays the foundation to build saas as efficiently as possible. Plug in your API keys, customize and ship. It has helped me saved hours setting up Stripe and authentication (which I think are the hardest).  

A paid version of this boilerplate supporting Stripe subscription payment is coming soon


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
    cp .env.example .env
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

## Why you shouldn't use this  




## Free Hosting on Linode 💰

- Hosting: $10/month (Get $60 credit on Linode with my [referral link](https://www.linode.com/lp/refer/?r=9ff0cd12e24c4e14bb041fd505242e605d1cc36d)


&nbsp;


## Contact me 📧

- [X](https://x.com/joji_jiji)
- [![Paid](https://img.shields.io/badge/Paid-Boilerplate-pink)](https://hero.codes/) **4 MORE App Templates to make M0N3Y 🤑🤑** 👉 [Check It Out!](https://hero.codes/)  

&nbsp;


P.S. If you like my project, a ⭐ would mean a lot to me, cheers! 🍻


