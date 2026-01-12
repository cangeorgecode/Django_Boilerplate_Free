# ── Builder stage ───────────────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ── Final stage ─────────────────────────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --system --uid 1000 --create-home appuser

WORKDIR /app

# Copy wheels + install deps (as root)
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Pre-create staticfiles dir and give ownership to appuser BEFORE copying code
RUN mkdir -p /app/staticfiles && \
    chown -R appuser:appuser /app/staticfiles

# Copy the rest of the project (chown to appuser)
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Set settings module (you already have this, keep it)
ENV DJANGO_SETTINGS_MODULE=proj.settings

RUN SECRET_KEY="nothing-for-build" python manage.py tailwind build --no-input

# Now collectstatic runs as appuser, and it can write to /app/staticfiles
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "proj.wsgi:application"]