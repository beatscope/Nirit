# nirit/views.py
import logging
import json
import operator
import re
import requests
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.template import RequestContext, loader
from django.conf import settings
from nirit.models import Building, Notice, Organization, OToken, UserProfile
from nirit.manager import ModelManager
from nirit.forms import CompanyForm, MemberForm, UserForm, SignUpForm
from nirit.utils import get_profile
from nirit.fixtures import Message

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

def sign_up(request):
    explanation = ''
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.get_profile().company:
                # Staff User created
                # Notify company Owner/Rep of new Staff sign-up
                company = user.get_profile().company
                subject = 'A new member has just joined {}'.format(company.name)
                data = {
                    'name': user.get_full_name(),
                    'company': company.name,
                    'link': '{}/company/{}/{}/staff'.format(settings.HOST, company.slug, company.codename)
                }
                text_content = Message().get('email_sign_up_success_text', data)
                html_content = Message().get('email_sign_up_success_html', data)
                company.mail_editors(subject, text_content, html_content)
                return HttpResponseRedirect('/member/sign-up/complete')
            else:
                # Owner User created
                # Send activation email
                subject = 'Activate your Nirit account'
                from_email = settings.EMAIL_FROM
                to = form.cleaned_data['email']
                data = {
                    'first_name': form.cleaned_data['first_name'],
                    'link': '{}/member/sign-up/activate?token={}'.format(settings.HOST, form.cleaned_data['auth_code'])
                }
                text_content = Message().get('email_activation_required_text', data)
                html_content = Message().get('email_activation_required_html', data)
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                return HttpResponseRedirect('/member/sign-up/activation-required')
    else:
        form = SignUpForm()
        explanation = Message().get('welcome')

    t = loader.get_template('registration/sign_up.html')
    c = RequestContext(request, {
        'form': form,
        'explanation': explanation
    })
    return HttpResponse(t.render(c))

def sign_up_complete(request):
    t = loader.get_template('registration/sign_up_complete.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))

def sign_up_activation_required(request):
    t = loader.get_template('registration/sign_up_activation_required.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))

def sign_up_activate(request):
    form = None
    context = {}
    if request.GET.has_key('token'):
        token = request.GET['token']
        try:
            t = OToken.objects.get(key=token)
        except OToken.DoesNotExist:
            context['status'] = 'FAILED'
        else:
            if t.redeemed:
                context['status'] = 'REDEEMED'
            else:
                # Log the user in
                user = t.user
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user)
                context['status'] = 'ACTIVATED'

                # This is the one-time chance for the user to create a company
                # The Company creation form is a slimmed-down versio of the Company Edit form
                # (only required information is desplayed, so that the same form class can be used)
                if request.method == 'POST':
                    form = CompanyForm(request.POST)
                    if form.is_valid():
                        company = form.save()

                        # Assign user to the company
                        profile = user.get_profile()
                        profile.company = company
                        profile.save()

                        # Assign company to building
                        t.building.organizations.add(company)

                        # Flag token as redeemed 
                        t.redeemed = True
                        t.save()

                        # Post INTRO notice to board
                        # ignore SSL Certificate verification when DEBUG in True
                        verify = not settings.DEBUG
                        # verification is token-based
                        # use the sysadmin token
                        token = get_profile(User.objects.get(pk=1))['token']
                        headers = {
                            'referer': settings.API_HOST,
                            'content-type': 'application/json',
                            'authorization': 'Token {}'.format(token)
                        }
                        data = {
                            'subject': '{} has just joined Nirit'.format(company.name),
                            'buildings': [t.building.codename],
                            'type': '{}'.format(Notice.INTRO)
                        }
                        r = requests.post("https://{}/api/notices/post".format(request.META['HTTP_HOST']),
                                          verify=verify,
                                          headers=headers,
                                          data=json.dumps(data))

                        # Notify Building Managers and Admins
                        subject = 'A new Company has just joined Nirit'
                        data = {
                            'name': company.name,
                            'link': '{}/company/{}/{}'.format(settings.HOST, company.slug, company.codename)
                        }
                        text_content = Message().get('email_new_company_text', data)
                        html_content = Message().get('email_new_company_html', data)
                        mail_admins(subject, text_content, html_message=html_content)
                        t.building.mail_managers(subject, text_content, html_content)

                        # Finally, redirect to company page
                        destination = '/company/{}/{}'.format(company.slug, company.codename)
                        return HttpResponseRedirect(destination)
                else:
                    form = CompanyForm()
    else:
        context['status'] = 'FAILED'

    if form:
        context['form'] = form
    t = loader.get_template('registration/sign_up_activate.html')
    c = RequestContext(request, context)
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

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # ignore SSL Certificate verification when DEBUG in True
    verify = not settings.DEBUG
    # verification is session-based
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }

    # Make an OPTIONS request to retrieve the full list of Notices for this user 
    r = requests.options("https://{}/api/notices".format(request.META['HTTP_HOST']), verify=verify, cookies=cookies)
    try:
        d = json.loads(r.text)
        context['notices'] = json.dumps(d['results']['notices'])
        context['types'] = json.dumps(d['types'])
        context['types_escaped'] = d['types']
        context['count'] = int(d['results']['all'])
    except IndexError:
        context['notices'] = '{}'
        context['types'] = '{}'
        context['types_escaped'] = {}
        context['count'] = 0
    
    # Load Building's first Notices
    url = "https://{}/api/notices/?building={}".format(request.META['HTTP_HOST'], building.codename)
    if request.GET.has_key('filter'):
        # when filters are provided, we also pass in the username to the API query
        url += '&member=' + request.user.username
        url += '&filter=' + request.GET['filter']
        # we also add it to the context for the template to use
        context['filter'] = request.GET['filter']
    response = requests.get(url, verify=verify, cookies=cookies)
    context['data'] = response.text

    # Add statistics
    context['stats'] = {
        'organizations': building.organizations.exclude(status=Organization.BANNED).count()
    }
    try:
        notice_count = json.loads(response.text)['count']
    except ValueError:
        notice_count = 0
    context['stats']['notices'] = notice_count

    # Convert logged-in user profile data into lists of IDs
    # used by the Board JS App for filtering
    profile = get_profile(request.user)
    if profile.has_key('starred'):
        context['starred'] = [int(n.id) for n in profile['starred']]
    else:
        context['starred'] = []

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

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

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

    # use Proxy API to return the grouped results
    url = "https://{}/api/companies/{}/{}".format(request.META['HTTP_HOST'], building.codename, group)
    if request.GET.has_key('page'):
        url += '?page=' + request.GET['page']
    # ignore SSL Certificate verification when DEBUG in True
    verify = not settings.DEBUG
    # verification is session-based
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }
    response = requests.get(url, verify=verify, cookies=cookies)
    context['data'] = response.text

    t = loader.get_template('nirit/directory.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def company_set_status(request, codename, action):
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check the user is a Building Manager
    if not 'Building Manager' in [g['name'] for g in request.user.groups.values('name')]:
        raise PermissionDenied

    # Check action
    if action not in ('activate', 'ban'):
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Unknown Action.'
        }), mimetype="application/json")

    try:
        company = Organization.objects.get(codename=codename)
        if action == 'activate':
            company.status = Organization.VERIFIED
        elif action == 'ban':
            company.status = Organization.BANNED
        company.save()
    except Organization.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({
            'status': '404',
            'reason': 'Unknown Company.'
        }), mimetype="application/json")

    response = HttpResponse(json.dumps({
        'status': '200',
        'data': {
            'company': codename,
            'action': action
        }
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


@login_required
def company_api(request, codename, group):
    """
    Organizations API proxy.
    Uses the Organizations API, and groups the results.

    """
    building = get_object_or_404(Building, codename=codename)

    # Check the user is a member of this building
    if request.user not in building.members:
        raise PermissionDenied

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Filter Companies
    url = "https://{}/api/organizations?building={}".format(request.META['HTTP_HOST'], building.codename)
    # add ordering
    url = "{}&{}={}".format(url, 'order-by', group)
    if request.GET.has_key('page'):
        url += '&page=' + request.GET['page']
    # ignore SSL Certificate verification when DEBUG in True
    verify = not settings.DEBUG
    # verification is session-based
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }
    response = requests.get(url, verify=verify, cookies=cookies)

    # group results by label
    data = json.loads(response.text)
    groups = []
    index = -1
    previous_value = None
    for result in data['results']:
        # use the first letter as the alphabetical group
        # otherwise, the label is the group name
        if group == 'name':
            label = result[group][:1]
        else:
            label = result[group]
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
    data['results'] = groups

    # override pagination links
    if data.has_key('next') and data['next']:
        next_page = re.search(r'&page=(?P<page>\d+)', data['next'])
        if next_page is not None:
            next_page = next_page.group('page')
            data['next'] = request.META['PATH_INFO'] + '?page=' + next_page

    # convert to JSON string before sending to the template
    return HttpResponse(json.dumps(data), mimetype='application/json')


@login_required
@ensure_csrf_cookie
def user_profile(request, username=None):
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check member being viewed
    # logged-in user or other?
    if username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404
        else:
            member = user
            profile = get_profile(user)
    else:
        user = request.user
        profile = get_profile(request.user)

    # ignore SSL Certificate verification when DEBUG in True
    verify = not settings.DEBUG
    # verification is session-based
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }

    # Make an OPTIONS request to retrieve the full list of Notices for this user
    r = requests.options("https://{}/api/notices".format(request.META['HTTP_HOST']), verify=verify, cookies=cookies)
    try:
        notices = json.dumps(json.loads(r.text)['results']['notices'])
    except (IndexError, ValueError):
        notices = '{}'

    # Load user's Notices
    url = "https://{}/api/notices/?member={}".format(request.META['HTTP_HOST'], user.username)
    response = requests.get(url, verify=verify, cookies=cookies)

    # Convert logged-in user starred notices into list of IDs
    # used by the Board JS App
    user_profile = get_profile(request.user)
    if user_profile.has_key('starred'):
        starred = [int(n.id) for n in user_profile['starred']]
    else:
        starred = []

    context = {
        'member': user,
        'profile': profile,
        'data': response.text,
        'starred': starred,
        'notices': notices
    }

    # Add companies approval
    #   - for Building Managers
    #   - only on member's own page
    if user == request.user:
        logger.debug('Building Manager' in [g['name'] for g in user.groups.values('name')])
        if profile.has_key('active_building') and 'Building Manager' in [g['name'] for g in user.groups.values('name')]:
            context['companies_awaiting'] = profile['active_building'].get_pending_companies()

    # Add staff awaiting approval
    #   - for Editors
    #   - only on member's own page
    if user == request.user:
        if profile.has_key('company') and profile['company'].is_editor(user):
            context['staff_awaiting'] = profile['company'].get_staff_awaiting()

    t = loader.get_template('nirit/user_profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def user_set_status(request, username, action):
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check the user is an Editor
    if not request.user.get_profile().company.is_editor(request.user):
        raise PermissionDenied

    # Check action
    if action not in ('activate', 'ban'):
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Unknown Action.'
        }), mimetype="application/json")

    try:
        user = User.objects.get(email=username)
        profile = user.get_profile()
        if action == 'activate':
            profile.status = UserProfile.VERIFIED
        elif action == 'ban':
            profile.status = UserProfile.BANNED
        profile.save()
    except User.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({
            'status': '404',
            'reason': 'Unknown User.'
        }), mimetype="application/json")

    response = HttpResponse(json.dumps({
        'status': '200',
        'data': {
            'username': username,
            'action': action
        }
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


@login_required
def user_profile_edit(request):
    """
    A user profile can only be edited by the user.

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # add the forms
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        # do NOT handle files in this form, as they are being uploaded via AJAX
        member_form = MemberForm(request.POST, instance=request.user.get_profile())
        if user_form.is_valid():
            # check member form
            if member_form.is_valid():
                # save the user model through the form instance
                user_form.save()
                # save the profile model directly,
                # to avoid re-submitting the file (which would be empty at this point)
                # we do this to avoid creating the file twice
                member_form.instance.job_title = member_form.cleaned_data['job_title']
                member_form.instance.bio = member_form.cleaned_data['bio']
                if request.POST.has_key('thumbnail') and request.POST['thumbnail']:
                    # if a new image was uploaded, use this one instead
                    member_form.instance.thumbnail = request.POST['thumbnail'].split(settings.MEDIA_URL)[1]
                else:
                    # otherwise use the current image
                    member_form.instance.thumbnail = member_form.cleaned_data['thumbnail']
                member_form.instance.save()
                # all done, redirect to the profile page
                destination = '/member/account'
                return HttpResponseRedirect(destination)
    else:
        user_form = UserForm(instance=request.user)
        member_form = MemberForm(instance=request.user.get_profile())

    # load template
    t = loader.get_template('nirit/user_profile_edit.html')
    c = RequestContext(request, {
        'member': request.user,
        'profile': get_profile(request.user),
        'user_form': user_form,
        'member_form': member_form
    })
    return HttpResponse(t.render(c))


@login_required
def set_preference(request, setting, value):
    if setting == 'network':
        try:
            organization = Organization.objects.get(codename=value)
        except Organization.DoesNotExist:
            raise Http404
        else:
            manager = ModelManager()
            results = manager.set_preference(user=request.user.username, preference='network', value=organization.id)
    elif setting == 'starred':
        try:
            notice = Notice.objects.get(pk=value)
        except Notice.DoesNotExist:
            raise Http404
        else:
            manager = ModelManager()
            results = manager.set_preference(user=request.user.username, preference='starred', value=notice.id)
    else:
        return HttpResponseBadRequest(json.dumps({
                    'status': '400',
                    'reason': 'Unknown Setting.'
               }), mimetype="application/json")
    
    response = HttpResponse(json.dumps(results), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


@login_required
def company(request, codename):
    """
    A company can be viewed by all of the Building's members.
    The 'Edit' button will be made available to company editors only.

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    context = {}
    organization = get_object_or_404(Organization, codename=codename)
    context['organization'] = organization
    context['staff'] = organization.members.all()[:4]

    # check the user is a member of the building this organization belongs to
    allowed = False
    for building in Building.objects.filter(organizations=organization):
        if request.user in building.members:
            allowed = True
    if not allowed:
        raise PermissionDenied

    # add whether the user is a company editor to the context
    context['is_user_editor'] = organization.is_editor(request.user)

    # Load company Notices
    url = "https://{}/api/notices/?company={}".format(request.META['HTTP_HOST'], organization.codename)
    verify = not settings.DEBUG # ignore SSL Certificate verification when DEBUG in True
    # verification is session-based
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }
    response = requests.get(url, verify=verify, cookies=cookies)
    context['notices'] = json.loads(response.text)['results'][:2]

    # load template
    t = loader.get_template('nirit/company_profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def company_staff(request, codename):
    """
    Company staff page.
    Same permissions as the company home page.

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    context = {}
    organization = get_object_or_404(Organization, codename=codename)
    context['organization'] = organization
    context['staff'] = organization.members.all()

    # check the user is a member of the building this organization belongs to
    allowed = False
    for building in Building.objects.filter(organizations=organization):
        if request.user in building.members:
            allowed = True
    if not allowed:
        raise PermissionDenied

    # Load company Notices
    url = "https://{}/api/notices/?company={}".format(request.META['HTTP_HOST'], organization.codename)
    verify = not settings.DEBUG # ignore SSL Certificate verification when DEBUG in True
    # verification is session-based
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }
    response = requests.get(url, verify=verify, cookies=cookies)

    # Add statistics
    context['stats'] = {
        'members': organization.members.all(),
        'notices': json.loads(response.text),
        'expertise': organization.expertise.all()
    }

    # load template
    t = loader.get_template('nirit/company_profile_staff.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def company_board(request, codename):
    """
    Company board page.
    Same permissions as the company home page.

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    context = {}
    organization = get_object_or_404(Organization, codename=codename)
    context['organization'] = organization
    context['staff'] = organization.members.all()

    # check the user is a member of the building this organization belongs to
    allowed = False
    for building in Building.objects.filter(organizations=organization):
        if request.user in building.members:
            allowed = True
    if not allowed:
        raise PermissionDenied

    # ignore SSL Certificate verification when DEBUG in True
    verify = not settings.DEBUG
    # verification is session-based
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }

    # Make an OPTIONS request to retrieve the full list of Notices for this user
    r = requests.options("https://{}/api/notices".format(request.META['HTTP_HOST']), verify=verify, cookies=cookies)
    try:
        context['notices'] = json.dumps(json.loads(r.text)['results']['notices'])
    except IndexError:
        context['notices'] = '{}'

    # Load company Notices
    url = "https://{}/api/notices/?company={}".format(request.META['HTTP_HOST'], organization.codename)
    response = requests.get(url, verify=verify, cookies=cookies)
    context['data'] = response.text

    # Convert logged-in user starred notices into list of IDs
    # used by the Board JS App
    profile = get_profile(request.user)
    if profile.has_key('starred'):
        context['starred'] = [int(n.id) for n in profile['starred']]
    else:
        context['starred'] = []

    # Add statistics
    context['stats'] = {
        'members': organization.members.all(),
        'notices': json.loads(response.text),
        'expertise': organization.expertise.all(),
    }

    # load template
    t = loader.get_template('nirit/company_profile_board.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def company_edit(request, codename):
    """
    A company can be edited by:
        - Company Owner
        - Company rep

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    context = {}
    organization = get_object_or_404(Organization, codename=codename)
    context['organization'] = organization

    # check permissions
    allowed = False
    # 1. is user a member of staff?
    if not organization.is_staff(request.user):
        raise PermissionDenied
    # 2. is user an Owner or Rep for this company (i.e. a company editor)?
    if not organization.is_editor(request.user):
        raise PermissionDenied

    # user is allowed to edit the company
    # add the Organization form
    if request.method == 'POST':
        # do NOT handle files in this form, as they are being uploaded via AJAX
        form = CompanyForm(request.POST, instance=organization)
        if form.is_valid():
            # save the model directly,
            # to avoid re-submitting the file (which would be empty at this point)
            # we do this to avoid creating the file twice
            form.instance.floor = form.cleaned_data['floor']
            form.instance.description = form.cleaned_data['description']
            form.instance.founded = form.cleaned_data['founded']
            form.instance.expertise = form.cleaned_data['expertise']
            form.instance.department = form.cleaned_data['department']
            form.instance.size = form.cleaned_data['size']
            if request.POST.has_key('image') and request.POST['image']:
                # if a new image was uploaded, use this one instead
                form.instance.image = request.POST['image'].split(settings.MEDIA_URL)[1]
            else:
                # otherwise, use current image
                form.instance.image = form.cleaned_data['image']
            # the same logic applies for the logo and square_logo fields
            if request.POST.has_key('logo') and request.POST['logo']:
                form.instance.logo = request.POST['logo'].split(settings.MEDIA_URL)[1]
            else:
                form.instance.logo = form.cleaned_data['logo']
            if request.POST.has_key('square_logo') and request.POST['square_logo']:
                form.instance.square_logo = request.POST['square_logo'].split(settings.MEDIA_URL)[1]
            else:
                form.instance.square_logo = form.cleaned_data['square_logo']
            form.instance.save()
            # all done, redirect to company page
            destination = '/company/{}/{}'.format(organization.slug, organization.codename)
            return HttpResponseRedirect(destination)
    else:
        form = CompanyForm(instance=organization)
    context['form'] = form

    # load template
    t = loader.get_template('nirit/company_profile_edit.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))
