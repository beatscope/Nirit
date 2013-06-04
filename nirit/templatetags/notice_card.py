# nirit/templatetags/notice_card.py
"""
Notice Card Template Tag.

"""
import logging
from django import template
from nirit.utils import build_notice_card
register = template.Library()

logger = logging.getLogger('nirit.templatetags')


@register.tag(name="notice_card")
def do_show_notice_card(parser, token):
    return NoticeCardNode()

class NoticeCardNode(template.Node):
    def render(self, context):
        data = {}
        user = context['user']
        if user.is_authenticated:
            notice = context['card']
            data['user'] = user
            data['account'] = context['account']
            notice_data = build_notice_card(notice)
            data.update(notice_data)
        t = template.loader.get_template('nirit/notice_card.html')
        return t.render(template.Context(data, autoescape=context.autoescape))
