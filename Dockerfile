# ── Builder stage: Install Node.js + build Tailwind ─────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Node.js (required for django-tailwind's npm-based build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy & install Python deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy full project (includes tailwind.config.js, package.json, theme/, etc.)
COPY . .

# IMPORTANT: cd into the Tailwind npm directory where package.json & lockfile live
WORKDIR /app/theme/static_src

# Install npm dependencies (tailwind, postcss, etc.)
RUN npm ci

# === DEBUG: Helpful output to verify setup during build (keep for now) ===
RUN echo "\n=== DEBUG: Project structure around theme ===" && \
    find . -path "./theme" -type d -print && \
    echo "\n=== Files in theme/static_src/ ===" && \
    ls -la theme/static_src/ || echo "theme/static_src/ not found" && \
    echo "\n=== tailwind.config.js location and content ===" && \
    find . -name "tailwind.config.js" -exec cat {} \; || echo "tailwind.config.js not found" && \
    echo "\n=== Before build: theme/static/css/dist/ ===" && \
    mkdir -p theme/static/css/dist && ls -la theme/static/css/dist/ && \
    echo "\n=== RUNNING: python manage.py tailwind build ===" && \
    SECRET_KEY="dummy-for-build" python manage.py tailwind build --no-input || echo "tailwind build FAILED" && \
    echo "\n=== After build: theme/static/css/dist/ ===" && \
    ls -la theme/static/css/dist/ || echo "dist dir still missing/empty" && \
    echo "\n=== Final search for generated styles.css ===" && \
    find /app -name "styles.css" -type f

# ── Final stage: Lightweight runtime ─────────────────────────────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --system --uid 1000 --create-home appuser

WORKDIR /app

# Copy wheels/deps from builder (if you had a separate wheel stage, merge here)
# But since builder already installed deps, we can copy the whole /app (including built CSS)
COPY --from=builder /app /app

# Pre-create dirs & fix ownership (important for collectstatic + appuser)
RUN mkdir -p /app/staticfiles /app/logs && \
    chown -R appuser:appuser /app/staticfiles /app/logs && \
    chmod -R 775 /app/logs

# Switch to non-root
USER appuser

# Collect static files (now includes the freshly built Tailwind CSS)
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "proj.wsgi:application"]