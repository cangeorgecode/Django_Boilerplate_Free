# ── Builder stage ───────────────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies for Python packages + curl for Node.js setup
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

# Install Node.js 22.x LTS (modern Nodesource method with keyring)
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

# Copy wheels + install deps (as root)
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Pre-create staticfiles dir
RUN mkdir -p /app/staticfiles

COPY . .

# Now install npm deps as root (after code is copied)
RUN cd /app/theme/static_src && npm install

RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set settings module
ENV DJANGO_SETTINGS_MODULE=proj.settings

# Now collectstatic runs as appuser
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "proj.wsgi:application"]