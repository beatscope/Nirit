# nirit/admin.py
""" Enables data browsing for System Admin """
from django.contrib import databrowse
from django.contrib.auth.models import User, Group
from nirit.models import Building, Organization, Notice

databrowse.site.register(User, Group, Building, Organization, Notice)
