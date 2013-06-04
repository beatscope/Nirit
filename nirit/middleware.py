"""
Nirit Middleware.

    - Set active Building.
    - Set META data.
    - Set active Menu item.

"""
import datetime
import logging
from django.http import HttpResponseRedirect
from nirit.manager import ModelManager
from nirit.models import Building, Organization

logger = logging.getLogger('nirit.middleware')


class NiritMiddleware(object):

    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated():
            if request.GET.has_key('set-active-building'):
                # Active building reset requested
                manager = ModelManager()
                try:
                    building = Building.objects.get(codename=request.GET['set-active-building'])
                except Building.DoesNotExist:
                    pass
                else:
                    res = manager.set_preference(user=request.user.username, preference='active-building', value=building.id)
                    return HttpResponseRedirect(request.path)
            elif not request.user.get_profile().building:
                # Default active building to the first user's building if none set
                manager = ModelManager()
                try:
                    organizations = Organization.objects.filter(members=request.user)
                    buildings = []
                    for org in organizations:
                        buildings.extend(org.building_set.all())
                    active_building = buildings[0]
                except IndexError:
                    pass
                else:
                    res = manager.set_preference(user=request.user.username, preference='active-building', value=active_building.id)
                    return HttpResponseRedirect(request.path)
        return response


def request(request):
    meta = {}

    if request.user.is_authenticated():
        meta['menu'] = [
            {'link': 'My Account', 'href': '/user/account'},
            {'link': 'Change Password', 'href': '/user/password/change'},
            {'link': 'Logout', 'href': '/logout'}
        ]
        meta['account'] = {}

        # Active Building
        if request.user.get_profile().building:
            meta['account']['active_building'] = request.user.get_profile().building
            # prepend building links to the user links
            links = [
                {'link': 'Notice Board', 'href': '/board/{}'.format(request.user.get_profile().building.link)},
                {'link': 'Directory', 'href': '/directory/{}'.format(request.user.get_profile().building.link)},
            ]
            meta['menu'] = links + meta['menu']

        # Highlight active menu item
        for i, l in enumerate([p for p in meta['menu'] if p['href'] not in ('/user/password/change', '/logout')]):
            path = request.path.split('/')[1]
            if '/{}/'.format(path) in l['href']:
                meta['menu'][i]['class'] = 'active'
                break

        if request.user.get_profile().networked.all():
            meta['account']['networked'] = request.user.get_profile().networked.count()

        if request.user.get_profile().starred.all():
            meta['account']['starred'] = request.user.get_profile().starred.count()

        roles = request.user.groups.all()
        meta['account']['roles'] = ", ".join([g.name for g in roles])

        organizations = Organization.objects.filter(members=request.user)
        meta['account']['organizations'] = organizations

        buildings = []
        for org in organizations:
            buildings.extend(org.building_set.all())
        meta['account']['buildings'] = buildings

    return meta
