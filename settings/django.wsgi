import inspect
import os
import socket
import sys
import django.core.handlers.wsgi

SCRIPT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(ROOT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.settings-' + socket.gethostname()
application = django.core.handlers.wsgi.WSGIHandler()
