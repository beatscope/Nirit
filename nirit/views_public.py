# nirit/views_public.py
import logging
import json
import operator
import requests
from django.core.exceptions import PermissionDenied
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext, loader
from django.conf import settings
from nirit.models import Page, UserProfile, Supplier
from nirit.fixtures import Message
from nirit import utils

logger = logging.getLogger('nirit.public')


def landing(request):
    context = {}
    if request.user.is_anonymous():
        if request.method == 'POST':
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                auth_login(request, form.get_user())
                if request.GET.has_key('next'):
                    return HttpResponseRedirect(request.GET['next'])
                return HttpResponseRedirect('/')
        else:
            form = AuthenticationForm()
        context['form'] = form
    else:
        # Redirect authenticated user to their primary space's Notice Board
        destination = 'board/{}'.format(request.user.get_profile().space.link)
        return HttpResponseRedirect(destination)

    t = loader.get_template('nirit/index.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


def sitemap(request):
    suppliers = Supplier.objects.all()
    t = loader.get_template('sitemap.xml')
    c = RequestContext(request, {
        'host': settings.HOST,
        'suppliers': suppliers,
    })
    return HttpResponse(t.render(c), mimetype="text/xml")


def page(request, page):
    p = get_object_or_404(Page, slug=page)
    t = loader.get_template('nirit/page.html')
    c = RequestContext(request, {
        'title': p.title,
        'body': p.body
    })
    return HttpResponse(t.render(c))


def supplier(request, slug):
    try:
        supplier = Supplier.objects.get(slug=slug)
    except Supplier.DoesNotExist:
        # when the slug does does not match, we attempt to find the closest match
        candidates = Supplier.objects.filter(slug__startswith=slug).values('id', 'location')
        if not candidates:
            raise Http404
        for candidate in candidates:
            # calculate distances
            if not candidate['location']:
                candidate['distance'] = 99999999999
            else:
                geocode = [float(c) for c in candidate['location'].split(',')]
                distance = utils.get_distance(geocode[0],
                                              geocode[1],
                                              request.user.get_profile().space.geocode.latitude,
                                              request.user.get_profile().space.geocode.longitude)
                candidate['distance'] = distance[1]
        candidates = sorted(candidates, key=operator.itemgetter('distance'))
        try:
            supplier = Supplier.objects.get(pk=candidates[0]['id'])
            url = '/supplier/{}'.format(supplier.slug)
            return redirect(url)
        except Exception as e:
            logger.error('Supplier slug detection failed. {}'.format(e))
            raise Http404

    back = None
    if request.GET.has_key('by'):
        back = '?by={}'.format(request.GET['by'])

    context = {
        'supplier': supplier,
        'back': back,
        'BING_MAPS_KEY': settings.BING_MAPS_KEY
    }

    if request.user.is_authenticated():
        # Authenticated user see the supplier board
        # which is the space board, filtered for @mention
        try:
            space = request.user.get_profile().space
            if not space:
                raise Exception
        except:
            pass

        # Check the user is a member of this space
        if request.user not in space.members:
            raise PermissionDenied

        # Check the user is active
        if not request.user.get_profile().status == UserProfile.VERIFIED:
            raise PermissionDenied

        context['space'] = space

        # The supplier @mention is the first part of the slug
        mention = supplier.slug.split('/')[0]
        context['mention'] = mention

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
        except Exception as e:
            context['notices'] = '{}'

        # Load Space's first Notices
        headers = {
            'referer': settings.API_HOST,
            'content-type': 'application/json',
            # use the logged-in user authorization token
            'authorization': 'Token {}'.format(request.user.get_profile().token)
        }
        params = {
            'space': space.codename,
            'member': request.user.get_profile().codename,
            'filter': 'mention',
            'mention': mention
        }
        url = "{}/notices".format(settings.API_HOST)
        response = requests.get(url, verify=False, headers=headers, params=params)
        context['data'] = response.text

    t = loader.get_template('nirit/supplier.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))
