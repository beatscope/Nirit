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
from nirit.models import Building, CompanyProfile

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
                    buildings = CompanyProfile.objects.filter(organization=company)
                    active_building = buildings[0].building
                except IndexError:
                    pass
                else:
                    res = manager.set_preference(user=request.user.username, preference='active-building', value=active_building.id)
                    return HttpResponseRedirect(request.path)
        return response


def request(request):
    meta = {}

    if request.user.is_authenticated():
        meta['menu'] = []

        # Building menu item
        # defaults to the user's default building
        if request.user.get_profile().building:
            meta['menu'].append({
                'link': 'Notice Board',
                'name': 'notice-board',
                'href': '/board/{}'.format(request.user.get_profile().building.link)
            })
            meta['menu'].append({
                'link': 'Directory', 
                'name': 'directory',
                'href': '/directory/{}'.format(request.user.get_profile().building.link)
            })

        # Add user's company
        if request.user.get_profile().company:
            meta['menu'].append({
                    'link': 'Company Profile',
                    'name': 'company',
                    'href': '/company/{}'.format(request.user.get_profile().company.link)
                })

        # Highlight active menu item
        for i, l in enumerate([p for p in meta['menu'] if p['href']]):
            path = request.path.split('/')[1]
            if '/{}/'.format(path) in l['href']:
                meta['menu'][i]['class'] = 'active'
                break

    return meta
