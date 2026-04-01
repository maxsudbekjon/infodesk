# =========================
# BASE IMAGE
# =========================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# =========================
# DEPENDENCIES
# =========================
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# =========================
# PROJECT
# =========================
COPY . .

RUN chmod +x /app/docker/prod/entrypoint.sh

# =========================
# DEFAULT
# =========================
ENTRYPOINT ["bash", "/app/docker/prod/entrypoint.sh"]