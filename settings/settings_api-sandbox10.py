from common import *

DEBUG = True

ADMINS = (
    ('Nirit API [dev]', 'engineering@beatscope.co.uk'),
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

ROOT_URLCONF = 'api.urls'

#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

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

LOGGING['loggers']['api']['level'] = 'DEBUG'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}
