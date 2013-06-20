# nirit/views.py
import json
import logging
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from nirit.models import Building, Organization
from nirit.api import NoticeAPI

logger = logging.getLogger('nirit.views')


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
    context['buildings'] = Building.objects.all()
    t = loader.get_template('nirit/index.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def user_account(request):
    t = loader.get_template('nirit/user_account.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))


@login_required
@ensure_csrf_cookie
def board(request, codename):
    context = {}
    building = get_object_or_404(Building, codename=codename)
    context['building'] = building
    # Check the user is a member of this building
    if request.user not in building.members:
        raise PermissionDenied
    # load Building's first Notices
    notices = building.notices.filter(is_reply=False).order_by('-created')
    context['cards'] = notices[:settings.BOARD_NOTICES]
    context['cards_count'] = notices.count()
    context['cards_range'] = settings.BOARD_NOTICES
    t = loader.get_template('nirit/board.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def directory(request, codename):
    context = {}
    building = get_object_or_404(Building, codename=codename)
    context['building'] = building
    # Check the user is a member of this building
    if request.user not in building.members:
        raise PermissionDenied
    context['tabs'] = [
        {'name': 'By Floor', 'href': '?sort=fl'},
        {'name': 'By Department', 'href': '?sort=dp'},
        {'name': 'Alphabetical', 'href': '?sort=ab'}
    ]
    # Set active tab
    context['display'] = 'floor'
    if request.GET.has_key('sort'):
        if request.GET['sort'] == 'dp':
            context['display'] = 'department'
            context['tabs'][1]['class'] = 'active'
        elif request.GET['sort'] == 'ab':
            context['display'] = 'alphabetical'
            context['tabs'][2]['class'] = 'active'
        else:
            context['tabs'][0]['class'] = 'active'
    else:
        context['tabs'][0]['class'] = 'active'
    # Set sort ordering
    context['organizations'] = building.organizations.all()
    if context['display'] == 'department':
        context['organizations'] = context['organizations'].order_by('department')
    elif context['display'] == 'alphabetical':
        context['organizations'] = context['organizations'].order_by('name')
    else:
        context['organizations'] = context['organizations'].order_by('floor')
    t = loader.get_template('nirit/directory.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))

@login_required
def company(request, codename):
    context = {}
    organization = get_object_or_404(Organization, codename=codename)
    context['organization'] = organization
    # Check the user is a member of the building this organization belongs to
    allowed = False
    for building in Building.objects.filter(organizations=organization):
        if request.user in building.members:
            allowed = True
    if not allowed:
        raise PermissionDenied
    t = loader.get_template('nirit/company_profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


def notices(request, object_code=None, action='view', start=0):
    """
    REST Notice API Wrapper.
    Provides HTTP GET/POST access to the Notice API.

    @param  object_code:    [GET] Building Codename or Notice ID
    @type   object_code:    string

    @param  action:         [GET] View notices ('view') or replies ('replies')
    @type   action:         string

    @param  start:          [GET] Index start
    @type   start:          integer

    """
    api = NoticeAPI()
    if request.method == 'POST':
        # POST request (new notice, or reply to a notice)
        subject = request.POST['subject'] if request.POST.has_key('subject') else None
        sender = request.user.username
        buildings = request.POST['buildings'] if request.POST.has_key('buildings') else None
        is_official = bool(int(request.POST['is_official'])) if request.POST.has_key('is_official') else False
        nid = int(request.POST['nid']) if request.POST.has_key('nid') else None
        data = api.post(subject=subject, sender=sender, buildings=buildings, is_official=is_official, nid=nid)
    else:
        # GET request (view notices for building, or view notice replies)
        replies_only = True if action == 'replies' else False
        data = api.get(object_code=object_code, start=start, replies_only=replies_only)
    c = RequestContext(request)
    response = render_to_response('nirit/default.json', {'data': json.dumps(data)}, context_instance=c)
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response
