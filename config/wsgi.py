
import os
import sys
import logging


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream=sys.stdout,
                    force=True)


from django.core.wsgi import get_wsgi_application

django_env = os.environ.get("DJANGO_ENV", "base").lower()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{django_env}")


logging.info("WSGI STARTED, django settings is %s", django_env)

application = get_wsgi_application()



