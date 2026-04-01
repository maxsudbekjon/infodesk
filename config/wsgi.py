
import os
import sys
import logging

from django.core.wsgi import get_wsgi_application

django_env = os.environ.get("DJANGO_ENV", "base").lower()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{django_env}")

application = get_wsgi_application()


logging.info("WSGI started, django settings is %s", django_env)

