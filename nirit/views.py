# nirit/views.py
import logging
import json
import operator
import re
import requests
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.conf import settings
from nirit.models import Space, UserProfile, CompanyProfile
from nirit import utils

logger = logging.getLogger('nirit.views')


@login_required
@ensure_csrf_cookie
def board(request, codename=None):
    context = {}
    if not request.user.get_profile().space:
        raise PermissionDenied
    if not codename:
        url = '/board/{}/{}'.format(request.user.get_profile().space.slug, request.user.get_profile().space.codename)
        return redirect(url)

    space = get_object_or_404(Space, codename=codename)

    # Check the user is a member of this space
    if request.user not in space.members:
        raise PermissionDenied

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    context['space'] = space

    # Make an OPTIONS request to retrieve the full list of Notices for this user 
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }
    url = "https://{}/api/notices".format(request.META['HTTP_HOST'])
    r = requests.options(url, verify=False, cookies=cookies)
    try:
        d = json.loads(r.text)
        context['notices'] = json.dumps(d['results']['notices'])
        context['types'] = json.dumps(d['types'])
        context['types_escaped'] = d['types']
        context['count'] = int(d['results']['all'])
    except Exception as e:
        context['notices'] = '{}'
        context['types'] = '{}'
        context['types_escaped'] = {}
        context['count'] = 0
    
    # Load Space's first Notices
    headers = {
        'referer': settings.API_HOST,
        'content-type': 'application/json',
        # use the logged-in user authorization token
        'authorization': 'Token {}'.format(request.user.get_profile().token)
    }
    params = {
        'space': space.codename
    }
    if request.GET.has_key('filter'):
        # when filters are provided, we also pass in the member to the API query
        params['member'] = request.user.get_profile().codename
        params['filter'] = request.GET['filter']
        # we also add it to the context for the template to use
        context['filter'] = request.GET['filter']
    url = "{}/notices".format(settings.API_HOST)
    response = requests.get(url, verify=False, headers=headers, params=params)
    context['data'] = response.text

    # Add statistics
    context['stats'] = {
        'organizations': space.space_profile.exclude(status=CompanyProfile.BANNED).count()
    }
    try:
        notice_count = json.loads(response.text)['count']
    except:
        notice_count = 0
    context['stats']['notices'] = notice_count

    t = loader.get_template('nirit/board.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def directory(request, codename=None):
    context = {}
    if not request.user.get_profile().space:
        raise PermissionDenied
    if not codename:
        url = '/directory/{}/{}'.format(request.user.get_profile().space.slug, request.user.get_profile().space.codename)
        return redirect(url)

    space = get_object_or_404(Space, codename=codename)

    # Check the user is a member of this space
    if request.user not in space.members:
        raise PermissionDenied

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    context['space'] = space
    context['tabs'] = [
        {'name': 'floor','label': 'By Floor', 'href': '?by=floor'},
        {'name': 'department', 'label': 'By Department', 'href': '?by=department'},
        {'name': 'name', 'label': 'Alphabetical', 'href': '?by=name'}
    ]
    if request.GET.has_key('by'):
        group = request.GET['by']
    else:
        # 'floor' is the default tab
        group = 'floor'
    context['group'] = group

    # Authentication is Token-based
    headers = {
        'referer': settings.API_HOST,
        'content-type': 'application/json',
        # use the logged-in user authorization token
        'authorization': 'Token {}'.format(request.user.get_profile().token)
    }

    # Fetch companies using Nirit API
    url = "{}/spaces/{}".format(settings.API_HOST, space.codename)
    response = requests.get(url, verify=False, headers=headers)
    data = json.loads(response.text)

    # order by group
    companies = data['organizations']
    companies = sorted(companies, key=operator.itemgetter(group))

    # group results by label
    groups = []
    index = -1
    previous_value = None
    for result in companies:
        # use the first letter as the alphabetical group
        # otherwise, the label is the group name
        if group == 'name':
            label = result[group][:1]
        elif group == 'floor':
            label = result['floor_tag']
        else:
            label = result[group]
        # group
        if label != previous_value:
            _group = {
                'label': label,
                'results': [
                    result
                ]
            }
            groups.append(_group)
            index += 1
            previous_value = label
        else:
            groups[index]['results'].append(result)

    # override the result list with the grouped list
    data['count'] = len(companies)
    data['results'] = groups

    context['data'] = json.dumps(data)

    t = loader.get_template('nirit/directory.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def amenities(request, codename=None):
    context = {}
    if not request.user.get_profile().space:
        raise PermissionDenied
    if not codename:
        url = '/amenities/{}/{}'.format(request.user.get_profile().space.slug, request.user.get_profile().space.codename)
        return redirect(url)

    space = get_object_or_404(Space, codename=codename)

    # Check the user is a member of this space
    if request.user not in space.members:
        raise PermissionDenied

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    context['space'] = space
    context['tabs'] = [
        {'name': 'distance','label': 'By Distance', 'href': '?by=distance'},
        {'name': 'type', 'label': 'By Type', 'href': '?by=type'},
        {'name': 'name', 'label': 'Alphabetical', 'href': '?by=name'},
        {'name': 'map', 'label': 'Map', 'href': '?by=map'}
    ]
    if request.GET.has_key('by'):
        group = request.GET['by']
    else:
        # 'distance' is the default tab
        group = 'distance'
    context['group'] = group
    
    # Authentication is Token-based
    headers = {
        'referer': settings.API_HOST,
        'content-type': 'application/json',
        # use the logged-in user authorization token
        'authorization': 'Token {}'.format(request.user.get_profile().token)
    }

    # Fetch suppliers using Nirit API
    url = "{}/suppliers/".format(settings.API_HOST)
    params = {
        'search': space.codename
    }
    response = requests.get(url, verify=False, headers=headers, params=params)
    data = json.loads(response.text)

    # Computed data
    for supplier in data:
        # determine supplier icon
        supplier['icon'] = re.sub(r'\s\s*', '-', supplier['type'].lower())
        # calculate distances
        if not supplier['geocode'][0] and not supplier['geocode'][1]:
            supplier['distance'] = 'N/A'
            supplier['distance-key'] = 99999999999
        else:
            # coming from the API, the geocode is a coma-separated string
            geocode = [float(c) for c in supplier['geocode'].split(',')]
            distance = utils.get_distance(geocode[0],
                                          geocode[1],
                                          space.geocode.latitude,
                                          space.geocode.longitude)
            # we use miles
            if distance[1] <= 1:
                supplier['distance'] = '{} mile'.format(round(distance[1], 1))
            else:
                supplier['distance'] = '{} miles'.format(round(distance[1], 1))
            supplier['distance-key'] = distance[1]

    # Sort results
    key = group if group not in ('map',) else 'distance'
    amenities = sorted(data, key=operator.itemgetter(key))

    # group results by label
    groups = []
    index = -1
    previous_value = None
    for result in amenities:
        # use the first letter as the alphabetical group
        # use just the one group for distance/map
        # otherwise, the label is the group
        if group == 'name':
            label = result[group][:1]
        elif group == 'distance':
            label = 'Distance'
        elif group == 'map':
            label = 'Map'
        else:
            label = result[group]
        # group
        if label != previous_value:
            _group = {
                'label': label,
                'results': [
                    result
                ]
            }
            groups.append(_group)
            index += 1
            previous_value = label
        else:
            groups[index]['results'].append(result)

    context['count'] = len(amenities)
    context['amenities'] = groups
    context['amenities_js'] = json.dumps(groups)
    context['BING_MAPS_KEY'] = settings.BING_MAPS_KEY

    t = loader.get_template('nirit/amenities.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))
