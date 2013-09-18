# Production Settings
from common import *

DEBUG = True
TEMPLATE_DEBUG = False

INTERNAL_IPS = ('127.0.0.1', '10.1.29.10', '10.1.29.248', '46.255.116.84')
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

HOST = 'https://nirit.co.uk'
API_HOST = 'https://api.nirit.co.uk'

ADMINS = (
    ('Nirit Support', 'support@nirit.co.uk'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'nirit',
        'USER': 'nirit_dba',
        'PASSWORD': 'watraK87ac9&raNABr&Na6=t?epRuF4Ez5P2$StugE@WUBeqe4ru8eP-96er=6ad',
        'HOST': '',
        'PORT': '',
    }
}

ROOT_URLCONF = 'nirit.urls'

MEDIA_ROOT = '/home/nirit/uploads'
FILEBROWSER_DIRECTORY = ''
MEDIA_URL = 'https://media.nirit.co.uk/'
STATIC_ROOT = '/home/nirit/static'
STATIC_URL = 'https://static.nirit.co.uk/'
STATICFILES_DIRS = (
    '/home/nirit/nirit_src/static_files',
)

SECRET_KEY = '(eav6j0nj!@x1t)u(uu3^5x3&j47+&4j3c%w&%#z0x$-m*umdj'

TEMPLATE_DIRS = (
    '/home/nirit/nirit_src/templates'
)

LOGGING['loggers']['nirit']['level'] = 'ERROR'

EMAIL_SUBJECT_PREFIX = '[NIRIT] '
SERVER_EMAIL = 'noreply@nirit.co.uk'
EMAIL_FROM = 'noreply@nirit.co.uk'
