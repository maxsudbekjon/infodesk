# Deployment

## Local development

1. Copy `env.example` to `.env`.
2. Start services:

```bash
docker compose up --build
```

## Production

1. Fill `.env` with real production values.
2. Set `DJANGO_ENV=prod`.
3. Set these values at minimum:
   - `SECRET_KEY`
   - `ALLOWED_HOSTS`
   - `CORS_ALLOWED_ORIGINS`
   - `CSRF_TRUSTED_ORIGINS`
   - `DB_TYPE=POSTGRES`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_HOST`
   - `DB_PORT`
4. Start production services:

```bash
docker compose -f docker-compose.prod.yaml up --build -d
```

## Health check

Use:

```bash
GET /apps/dashboard/health/
```
