from common import *

DEBUG = True

ADMINS = (
    ('Nirit [dev]', 'engineering@beatscope.co.uk'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'nirit',
        'USER': 'nirit_dba',
        'PASSWORD': 'pass',
        'HOST': '',
        'PORT': '',
    }
}

MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_ROOT = ''
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

SECRET_KEY = 'a7(8!)t4xp24020s^_usgh0hrfpy(b!n6&amp;1!32vme9s47vqbcr'

TEMPLATE_DIRS = (
    '/home/michael/projects/nirit/templates'
)

LOGGING['loggers']['nirit']['level'] = 'DEBUG'
