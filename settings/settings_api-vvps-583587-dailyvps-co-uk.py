from common import *

DEBUG = False
ALLOWED_HOSTS = ['api.nirit.co.uk']

ADMINS = (
    ('Nirit API', 'support@nirit.co.uk'),
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

ROOT_URLCONF = 'api.urls'

MEDIA_ROOT = '/home/nirit/uploads'
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

LOGGING['loggers']['api']['level'] = 'ERROR'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}
