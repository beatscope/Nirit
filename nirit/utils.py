# nirit/utils.py
"""
Common Utilities.

"""
import datetime
import logging
from django.utils.timesince import timesince
from django.utils.html import escape
from nirit.models import Organization

logger = logging.getLogger('nirit.utils')


def build_notice_card(notice, mimetype='object'):
    data = {}
    # DO NOT include the full Notice Object for JSON output
    if mimetype not in ('json',):
        data['card'] = notice
    data['id'] = notice.id
    data['subject'] = escape(notice.subject)
    data['type'] = notice.get_type_display()
    data['is_official'] = notice.is_official
    data['age'] = timesince(notice.created, datetime.datetime.now())
    data['replies_count'] = notice.get_replies().count()
    if notice.sender.is_superuser:
        data['sender'] = 'System Administrator'
    else:
        data['sender'] = notice.sender.get_full_name() \
                         if notice.sender.get_full_name() \
                         else notice.sender.username
    if not notice.sender.groups.filter(name='Staff').count():
        try:
            organization = Organization.objects.filter(members=notice.sender)[0]
            data['organization'] = organization.name
        except IndexError:
            pass
    return data
