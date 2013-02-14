__author__ = 'esteele'

from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/home/esteele/sensorsproject/sensors_project.sqlite',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        }
}

DEBUG = False
TEMPLATE_DEBUG = DEBUG

STATICFILES_DIRS += ('/home/esteele/sensorsproject/sensors/static',)
TEMPLATE_DIRS += ('/home/esteele/sensorsproject/templates',)

