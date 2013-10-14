import inspect
import os
import stat

DEBUG = False
TEMPLATE_DEBUG = False

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
AUTH_PROFILE_MODULE = 'nirit.UserProfile'

ADMINS = ()
DATABASES = {}
DATABASE_OPTIONS = {
    'use_unicode': True,
    'charset': 'utf8_general_ci'
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = ''

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'tkd2d)a%nhw+ay!zfogg&w0wrb1kdphia6)3r8id$mt_qwxqqu'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'nirit.middleware.request',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'nirit.middleware.NiritMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
)

TEMPLATE_DIRS = ()

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'grappelli',
    'filebrowser',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    #'django.contrib.humanize',
    'nirit',
    # requires south
    # @see http://south.readthedocs.org/en/latest/index.html
    'south',
    'rest_framework',
    'rest_framework.authtoken',
    'markitup',
    'debug_toolbar'
)

AUTHENTICATION_BACKENDS = (
    'nirit.auth.EmailBackend',
)

MARKITUP_FILTER = ('markdown.markdown', {'safe_mode': False})
MARKITUP_SET = 'markitup/sets/markdown'
MARKITUP_AUTO_PREVIEW = True
JQUERY_URL='js/jquery-1.9.1.min.js'

GRAPPELLI_ADMIN_TITLE = 'Nirit'

SCRIPT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
LOGFILENAME = os.path.abspath(os.path.join(SCRIPT_DIR, '../../runtime/runtime.log'))
LOGFILE = open(LOGFILENAME, 'a+')
try:
    # The file owner sets the permissions to 777 so every process can log to the same file
    os.chmod(LOGFILE.name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
except OSError:
    pass
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] %(asctime)s %(module)s: %(message)s'
        },
    },
    'handlers': {
        'log_to_file': {
            'class': 'logging.FileHandler',
            'filename': LOGFILE.name,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'nirit': {
            'handlers': ['log_to_file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'api': {
            'handlers': ['log_to_file'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
