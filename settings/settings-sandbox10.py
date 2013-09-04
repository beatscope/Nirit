from common import *

DEBUG = True

HOST = 'https://nirit.bsc-dev.com'
API_HOST = 'https://api.nirit.bsc-dev.com'

ADMINS = (
    ('Nirit Support', 'support@nirit.co.uk'),
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

ROOT_URLCONF = 'nirit.urls'

MEDIA_ROOT = '/home/michael/projects/nirit/uploads'
MEDIA_URL = 'https://media.nirit.bsc-dev.com/'
STATIC_ROOT = '/home/michael/projects/nirit/static'
STATIC_URL = 'https://static.nirit.bsc-dev.com/'
STATICFILES_DIRS = (
    '/home/michael/projects/nirit/nirit_src/static_files',
)

SECRET_KEY = 'a7(8!)t4xp24020s^_usgh0hrfpy(b!n6&amp;1!32vme9s47vqbcr'

TEMPLATE_DIRS = (
    '/home/michael/projects/nirit/nirit_src/templates'
)

LOGGING['loggers']['nirit']['level'] = 'DEBUG'

EMAIL_SUBJECT_PREFIX = '[NIRIT-DEV] '
SERVER_EMAIL = 'noreply@nirit.co.uk'
EMAIL_FROM = 'noreply@nirit.co.uk'
#EMAIL_HOST = 'localhost'
#EMAIL_PORT = 1025
#EMAIL_HOST_USER = 
#EMAIL_HOST_PASSWORD = 
#EMAIL_USE_TLS = True
