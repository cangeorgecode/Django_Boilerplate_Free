# Stage 1: Build Tailwind CSS
FROM python:3.12-slim AS builder

WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# Install npm deps
RUN npm ci

# === FULL DEBUG FOR TAILWIND BUILD ===
RUN echo "\n=== DEBUG: Project structure around theme ===" && \
    find . -path "./theme" -type d -print && \
    echo "\n=== Files in theme/static_src/ ===" && \
    ls -la theme/static_src/ || echo "theme/static_src/ not found" && \
    echo "\n=== tailwind.config.js location and content ===" && \
    find . -name "tailwind.config.js" -exec cat {} \; || echo "tailwind.config.js not found anywhere" && \
    echo "\n=== Input CSS file ===" && \
    find . -name "styles.css" -path "*/src/*" -exec head -20 {} \; || echo "src/styles.css not found" && \
    echo "\n=== Before build: theme/static/css/dist/ ===" && \
    mkdir -p theme/static/css/dist && ls -la theme/static/css/dist/ && \
    echo "\n=== RUNNING: python manage.py tailwind build ===" && \
    python manage.py tailwind build || echo "tailwind build FAILED" && \
    echo "\n=== After build: theme/static/css/dist/ ===" && \
    ls -la theme/static/css/dist/ || echo "dist dir still missing/empty" && \
    echo "\n=== Final search for any generated styles.css ===" && \
    find /app -name "styles.css" -type f

# Stage 2: Final image
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy built CSS (will fail build if missing — good for catching errors)
COPY --from=builder /app/theme/static/css/dist/styles.css /app/theme/static/css/dist/styles.css

RUN python manage.py collectstatic --noinput --verbosity=2

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --timeout 120 proj.wsgi:application"]