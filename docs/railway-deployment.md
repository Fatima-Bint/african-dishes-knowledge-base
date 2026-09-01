# Railway deployment

This project is ready to run as a Django web service on Railway with a Railway
PostgreSQL database.

## Railway service settings

Connect this repository to a new Railway service and use these commands.

Build command:

```text
python manage.py collectstatic --noinput
```

Start command:

```text
python manage.py migrate --noinput && python manage.py seed_demo && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
```

Healthcheck path:

```text
/
```

Keep Railway Serverless mode turned off so the public demo remains available
without a cold start.

## Required variables

Add these variables to the Django web service:

```text
DJANGO_SECRET_KEY=<a long random secret>
DJANGO_DEBUG=false
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Railway supplies `RAILWAY_PUBLIC_DOMAIN` automatically after a public domain is
generated. The Django settings add that hostname to `ALLOWED_HOSTS` and its
HTTPS origin to `CSRF_TRUSTED_ORIGINS`.

The following variables are optional:

```text
GEMINI_API_KEY=<only needed for AI-assisted extraction>
GEMINI_MODEL=<optional model override>
DEMO_VIDEO_ID=<11-character ID from the unlisted YouTube URL>
DJANGO_ALLOWED_HOSTS=<additional comma-separated hostnames>
DJANGO_CSRF_TRUSTED_ORIGINS=<additional comma-separated HTTPS origins>
```

Never commit real secret values or API keys to GitHub.
