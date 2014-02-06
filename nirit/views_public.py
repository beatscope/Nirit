# nirit/views_public.py
import logging
import json
import operator
import requests
import urllib
from django.core.exceptions import PermissionDenied
from django.core.validators import validate_email
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.core.mail import mail_admins
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.template import RequestContext, loader
from django.conf import settings
from nirit.models import Page, UserProfile, Membership, Supplier, Space, Geocode
from nirit.fixtures import Message
from nirit.forms import SupplierForm
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

        # 3 most recent Spaces
        context['spaces'] = Space.objects.all().order_by('-created')[:3]

    else:
        # Redirect authenticated user to their primary space's Notice Board
        # Owners and Affiliated Members have their primary Space automatically set on registration
        if request.user.get_profile().space:
            destination = 'board/{}'.format(request.user.get_profile().space.link)
        else:
            # This must be an Unaffiliated Member, who is not a Member of any Spaces yet.
            # Redirect to list of Spaces
            destination = 'spaces/'
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


def spaces(request):
    # Redirect POST requests to spaces with querystring
    if request.method == 'POST' and request.POST.has_key('search'):
        terms = urllib.quote(request.POST['search'])
        return HttpResponseRedirect('/spaces/?search={}'.format(terms))

    # Check for search parameter
    search_query = request.GET['search'] \
                   if request.GET.has_key('search') and request.GET['search'] \
                   else None
    title = 'Recently Added Spaces'
    postcode = None
    geocode = '0.0,0.0'
    if search_query:
        # we only handle valid postcodes for now
        postcode = utils.Extractor(search_query).extract_postcode()
        if postcode:
            title = 'Nearest Spaces'
            try:
                geocode = Geocode.objects.get(code=postcode)
            except Geocode.DoesNotExist:
                # If the geocode for this postcode has not yet been stored,
                # fetch it
                try:
                    point = utils.get_postcode_point(postcode)
                except:
                    # The function raises an Exception when the postcode does not exist
                    # we store the resulst as (0, 0) to avoid fetching the API every time
                    point = (0.0, 0.0)
                geocode = Geocode.objects.create(code=postcode, latitude=point[0], longitude=point[1])
            geocode = str(geocode)

    spaces = []
    # By default, we show most recent spaces
    for space in Space.objects.all().order_by('-created'):
        _space = {}
        # Filter out APPROVED and REJECTED memberships
        # for authenticated users
        if request.user.is_authenticated():
            if request.user in space.members:
                # No need to re-list spaces you are a member of
                continue
            try:
                membership = Membership.objects.get(space=space, member=request.user.get_profile())
                if membership.status == Membership.REJECTED:
                    # Hide spaces I have been rejected from
                    continue
                _space['pending'] = True if membership.status == Membership.PENDING else False
            except Membership.DoesNotExist:
                pass
        distance = space.get_distance(geocode)
        if distance:
            _space.update(distance)
        _space['space'] = space
        spaces.append(_space)

    # Order spaces by increasing distance if a search query was given
    if spaces and search_query:
        spaces = sorted(spaces, key=operator.itemgetter('distance'))
    # Only display first 6
    if spaces:
        spaces = spaces[:6]

    # Display Member spaces
    member_spaces = None
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        member_spaces = profile.get_spaces()

    context = {
        'title': title,
        'postcode': postcode,
        'spaces': spaces
    }
    if member_spaces:
        context['member_spaces'] = member_spaces
    t = loader.get_template('nirit/spaces.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


def spaces_awaiting_approval(request):
    t = loader.get_template('nirit/space-awaiting-approval.html')
    c = RequestContext(request)
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
            if not candidate['location'] or request.user.is_anonymous():
                candidate['distance'] = 99999999999
            else:
                geocode = [float(c) for c in candidate['location'].split(',')]
                space_geocode = [float(c) for c in request.user.get_profile().space.geocode.split(',')]
                distance = utils.get_distance(geocode[0],
                                              geocode[1],
                                              space_geocode[0],
                                              space_geocode[1])
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

    # add whether the user is a Space Manager,
    # i.e. whether he is allowed to request for new Amenities/Suppliers
    context['is_user_editor'] = True if 'Manager' in [g['name'] for g in request.user.groups.all().values('name')] else False
    context['form'] = SupplierForm(instance=supplier)

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


def action(request, action):
    """
    Handle public actions.
    Available through AJAX. POST only allowed.

    """
    if request.method == 'GET':
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Method Not Allowed.'
        }), mimetype="application/json")

    # Check email address is valid
    try:
        email = request.POST['email']
        validate_email(email)
    except Exception:
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Enter a valid email address.'
        }), mimetype="application/json")

    subject = 'Someone registered an interest to join Nirit'
    text_content = Message().get('email_register_interest_text', {'email': email})
    mail_admins(subject, text_content)

    response = HttpResponse(json.dumps({
        'status': '200',
        'action': action
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response
