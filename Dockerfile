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

# First, verify the theme directory structure
RUN echo "=== Theme directory structure ===" && \
    find /app/theme -type f -name "*.css" -o -name "*.js" -o -name "*.json" | sort && \
    echo "=== Checking static_src directory ===" && \
    ls -la /app/theme/static_src/

# Ensure the theme app is properly configured
WORKDIR /app/theme/static_src

# Install npm dependencies
RUN npm ci

# Create necessary directory for output
RUN mkdir -p ../static/css/dist

# Build Tailwind CSS
RUN SECRET_KEY="dummy-for-build" \
    DJANGO_SETTINGS_MODULE="proj.settings" \
    python /app/manage.py tailwind build --no-input

# Debug: Check what was built
RUN echo "=== After tailwind build ===" && \
    echo "Checking /app/theme/static/css/dist/:" && \
    ls -la /app/theme/static/css/dist/ && \
    echo "=== Full search for styles.css ===" && \
    find /app -name "styles.css" -type f

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

# Verify collected static files
RUN echo "=== Checking collected static files ===" && \
    find /app/staticfiles -name "*.css" -type f

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "proj.wsgi:application"]