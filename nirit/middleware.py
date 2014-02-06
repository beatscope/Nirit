"""
Nirit Middleware.

    - Set active Space.
    - Set META data.
    - Set active Menu item.

"""
import datetime
import logging
from django.http import HttpResponseRedirect
from django.conf import settings
from nirit.manager import ModelManager
from nirit.models import Space, CompanyProfile

logger = logging.getLogger('nirit.middleware')


class NiritMiddleware(object):

    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated():
            if request.GET.has_key('set-active-space'):
                # Active space reset requested
                manager = ModelManager()
                try:
                    space = Space.objects.get(codename=request.GET['set-active-space'])
                except Space.DoesNotExist:
                    pass
                else:
                    res = manager.set_preference(user=request.user.username, preference='active-space', value=space.id)
                    return HttpResponseRedirect(request.path)
            elif not request.user.get_profile().space:
                # Default active space to the company's first space if none set
                manager = ModelManager()
                try:
                    company = request.user.get_profile().company
                    if not company:
                        raise IndexError
                    spaces = CompanyProfile.objects.filter(organization=company)
                    active_space = spaces[0].space
                except IndexError:
                    pass
                else:
                    res = manager.set_preference(user=request.user.username, preference='active-space', value=active_space.id)
                    return HttpResponseRedirect(request.path)
        return response


def request(request):
    meta = {}

    if request.user.is_authenticated():
        meta['menu'] = []

        # Space menu item
        # defaults to the user's default space
        if request.user.get_profile().space:
            meta['menu'].append({
                'link': 'Notice Board',
                'name': 'notice-board',
                'href': '/board/{}'.format(request.user.get_profile().space.link)
            })
            meta['menu'].append({
                'link': 'Directory', 
                'name': 'directory',
                'href': '/directory/{}'.format(request.user.get_profile().space.link)
            })
            meta['menu'].append({
                'link': 'Amenities',
                'name': 'amenities',
                'href': '/amenities/{}'.format(request.user.get_profile().space.link)
            })

        # Add user's company
        if request.user.get_profile().company:
            meta['menu'].append({
                'link': 'Company Profile',
                'name': 'company',
                'href': '/company/{}'.format(request.user.get_profile().company.link)
            })
        else:
            meta['menu'].append({
                'link': 'Spaces',
                'name': 'directory',
                'href': '/spaces/'
            })

        # Highlight active menu item
        for i, l in enumerate([p for p in meta['menu'] if p['href']]):
            path = request.path.split('/')[1]
            if '/{}/'.format(path) in l['href']:
                meta['menu'][i]['class'] = 'active'
                break

    return meta
