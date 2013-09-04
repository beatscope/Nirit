"""
Nirit Middleware.

    - Set active Building.
    - Set META data.
    - Set active Menu item.

"""
import datetime
import logging
from django.http import HttpResponseRedirect
from django.conf import settings
from nirit.manager import ModelManager
from nirit.models import Building
from nirit.utils import get_profile

logger = logging.getLogger('nirit.middleware')


class NiritMiddleware(object):

    def process_response(self, request, response):
        # super users only access the B/O,
        # so skip request handling for them
        if hasattr(request, 'user') and request.user.is_authenticated() and not request.user.is_superuser:
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
                # Default active building to the company's first building if none set
                manager = ModelManager()
                try:
                    company = request.user.get_profile().company
                    if not company:
                        raise IndexError
                    buildings = company.building_set.all()
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
        meta['account'] = get_profile(request.user)
        meta['menu'] = []

        # Building menu item
        # defaults to the user's default building
        if meta['account'].has_key('active_building') and meta['account']['active_building']:
            # prepend building links to the user links
            links = [
                {
                    'link': 'Notice Board',
                    'name': 'notice-board',
                    'href': '/board/{}'.format(meta['account']['active_building'].link)
                },
                {
                    'link': 'Directory', 
                    'name': 'directory',
                    'href': '/directory/{}'.format(meta['account']['active_building'].link)
                },
            ]
            meta['menu'] = links + meta['menu']

        # Highlight active menu item
        for i, l in enumerate([p for p in meta['menu'] if p['href']]):
            path = request.path.split('/')[1]
            if '/{}/'.format(path) in l['href']:
                meta['menu'][i]['class'] = 'active'
                break

    return meta
