#!/bin/sh

set -e

echo "⏳ Waiting for PostgreSQL..."

while ! nc -z db 5432; do
  sleep 1
done

echo "✅ PostgreSQL started"

echo "📦 Apply migrations..."
python manage.py migrate --noinput

echo "📁 Collect static..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --log-level info