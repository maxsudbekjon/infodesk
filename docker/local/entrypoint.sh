#!/bin/sh

echo "WORKING DEVELOPMENT ENTRYPOINT..."

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

echo "🚀 Starting Django DEV server..."

exec python manage.py runserver 0.0.0.0:9898