# nirit/templatetags/building_card.py
"""
Building Card Template Tag.

"""
import datetime
from django import template
register = template.Library()

@register.tag(name="building_card")
def do_building_card(parser, token):
    return BuildingCardNode()

class BuildingCardNode(template.Node):
    def render(self, context):
        building = context['building']
        members = building.get_members_count()
        posts = building.notices.filter(date=datetime.datetime.now().date()).count()
        links = []
        user = context['user']
        if user.is_authenticated():
            if user in building.members:
                links.append({
                    'text': 'board',
                    'href': '/board/{}'.format(building.link)
                })
                links.append({
                    'text': 'directory',
                    'href': '/directory/{}'.format(building.link)
                })
            #else:
            #    links.append({
            #        'text': 'join',
            #        'href': '/'
            #    })
        else:
            links.append({
                'text': 'sign-up',
                'href': '/member/sign-up'
            })
        t = template.loader.get_template('nirit/building_card.html')
        return t.render(template.Context({
            'building': building,
            'members': members,
            'posts': posts,
            'links': links
        }, autoescape=context.autoescape))
