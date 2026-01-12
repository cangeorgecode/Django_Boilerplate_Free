# ── Builder stage: Build Tailwind (needs Node + Django to run manage.py tailwind build)
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (required so tailwind build can import Django/settings)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# cd to where package.json + lockfile live
WORKDIR /app/theme/static_src

RUN npm ci

# Debug (keep for now)
RUN echo "\n=== DEBUG in theme/static_src ===" && \
    ls -la && \
    echo "\n=== tailwind.config.js ===" && cat tailwind.config.js || echo "missing" && \
    echo "\n=== Before build ===" && mkdir -p ../static/css/dist && ls -la ../static/css/dist/ && \
    echo "\n=== Building Tailwind ===" && \
    SECRET_KEY="dummy-for-build" python /app/manage.py tailwind build --no-input || echo "FAILED" && \
    echo "\n=== After build ===" && ls -la ../static/css/dist/ && \
    find /app -name "styles.css"

# ── Final stage: Runtime (no Node.js bloat)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user
RUN useradd --system --uid 1000 --create-home appuser

WORKDIR /app

# Install Python deps (fresh for final image)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy code + built CSS from builder
COPY --from=builder /app /app

# Pre-create dirs with correct ownership
RUN mkdir -p /app/staticfiles /app/logs && \
    chown -R appuser:appuser /app/staticfiles /app/logs && \
    chmod -R 775 /app/logs

USER appuser

# Collectstatic (now Django is installed → works)
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "proj.wsgi:application"]