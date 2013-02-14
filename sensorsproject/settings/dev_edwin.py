__author__ = 'esteele'

# Common settings
from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/Users/esteele/Code/sensorsproject/sensors_project.sqlite',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        }
}

DEBUG = True
TEMPLATE_DEBUG = DEBUG

STATICFILES_DIRS += ('/Users/esteele/Code/sensorsproject/sensors/static',)
TEMPLATE_DIRS += ('/Users/esteele/Code/sensorsproject/templates',)


# Is it a problem that this is at the end rather than before sensors?
INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INTERNAL_IPS = ('127.0.0.1',)

