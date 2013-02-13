import os

if not os.environ["DJANGO_SETTINGS_MODULE"]:
    print "Django settings not specified. using dev settings"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensorsproject.dev_settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

