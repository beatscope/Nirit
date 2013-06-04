# nirit/views.py
import logging
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from nirit.models import Building, Organization

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
