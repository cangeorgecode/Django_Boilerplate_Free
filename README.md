# Django Micro-SaaS Boilerplate 🚀
### Building a portfolio of micro saas, so that I can spend time with family while still be able to provide financially 🎉 


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

This project is designed to run with **Docker** — the fastest and most reliable way to get everything working, including PostgreSQL, without installing Python, PostgreSQL, or any dependencies on your machine.

### Prerequisites

- **Docker** (with Docker Compose) installed  
  - Windows / macOS: Download from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
  - Linux: Follow your distro guide (e.g. `sudo apt install docker.io docker-compose` on Ubuntu)
- **Git** installed

**Note:** You do **not** need to install Python, PostgreSQL, Node.js, or any other tools locally — Docker handles everything.

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


## Free Hosting on Linode 💰

- Hosting: $10/month (Get $60 credit on Linode with my [referral link](https://www.linode.com/lp/refer/?r=9ff0cd12e24c4e14bb041fd505242e605d1cc36d)

&nbsp;


## Contact me 📧

Hi, my name is George. 👋 I taught myself python, django, bash, how to use Linux, while working a 9 to 5 (Damn! I am good!). I love to dabble in the terminal. I love doing this! My mission is simple:  

1. Build as many web apps as quickly as I can
2. Monetize

- [X](https://x.com/joji_jiji)
- [![Paid](https://img.shields.io/badge/Paid-Boilerplate-pink)](https://hero.codes/) **4 MORE App Templates to make M0N3Y 🤑🤑** 👉 [Check It Out!](https://hero.codes/)  

&nbsp;


P.S. Can I get a star ⭐ please? 🍻


