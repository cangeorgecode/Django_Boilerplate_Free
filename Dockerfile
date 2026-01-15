# ── Builder stage ───────────────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ── Final stage ─────────────────────────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Node.js 22.x (needed for tailwind build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --system --uid 1000 --create-home appuser

WORKDIR /app

# Copy and install Python dependencies
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Pre-create writable directories and set correct ownership
RUN mkdir -p /app/staticfiles \
             /app/media \
             /app/logs \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app/staticfiles /app/media /app/logs

# Copy project code
COPY . .

# Build frontend assets (tailwind/daisyUI)
RUN cd /app/theme/static_src && npm ci && npm run build

# Collect static files (runs as root, but directory is already owned by appuser)
RUN python manage.py collectstatic --noinput --clear

# Final ownership pass (covers anything created during collectstatic/build)
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Django settings
ENV DJANGO_SETTINGS_MODULE=proj.settings

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "proj.wsgi:application"]