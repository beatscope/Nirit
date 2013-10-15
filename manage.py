#!/usr/bin/env python
import inspect
import os
import re
import socket
import sys
from django.core.management import execute_from_command_line

SCRIPT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(ROOT_DIR)

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.nirit_settings'
    execute_from_command_line(sys.argv)
