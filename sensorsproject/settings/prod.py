__author__ = 'esteele'

# Common settings
from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'esteele_sensors_sensors',
        'USER': get_env_variable("SENSORS_DB_USER"),
        'PASSWORD': get_env_variable("SENSORS_DB_PASSWORD"),
        'HOST': 'localhost',
        'PORT': '',
    }
}

DEBUG = False
TEMPLATE_DEBUG = DEBUG
