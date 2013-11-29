# nirit/views_company.py
import logging
import json
import re
import requests
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext, loader
from django.utils.html import strip_tags, linebreaks
from django.conf import settings
from nirit.models import Organization, UserProfile, CompanyProfile, OToken
from nirit.forms import CompanyForm
from nirit.fixtures import Message
from nirit import utils

logger = logging.getLogger('nirit.views')


@login_required
def set_status(request, codename, action):
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check the user is a Manager
    if not 'Manager' in request.user.get_profile().roles:
        raise PermissionDenied

    # Check action
    if action not in ('activate', 'ban'):
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Unknown Action.'
        }), mimetype="application/json")

    try:
        company = Organization.objects.get(codename=codename)
        company_profile = CompanyProfile.objects.get(space=request.user.get_profile().space,\
                                                     organization=company)
        if action == 'activate':
            company_profile.status = CompanyProfile.VERIFIED
        elif action == 'ban':
            company_profile.status = CompanyProfile.BANNED
        company_profile.save()
    except (Organization.DoesNotExist, CompanyProfile.DoesNotExist):
        return HttpResponseBadRequest(json.dumps({
            'status': '404',
            'reason': 'Unknown Company.'
        }), mimetype="application/json")

    response = HttpResponse(json.dumps({
        'status': '200',
        'data': {
            'codename': codename,
            'action': action
        }
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


@login_required
def profile(request, codename=None):
    """
    A company can be viewed by all of the Space's members.
    The 'Edit' button will be made available to company editors only.

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied
    if not codename:
        url = '/company/{}/{}'.format(request.user.get_profile().company.slug, request.user.get_profile().company.codename)
        return redirect(url)

    context = {}
    organization = get_object_or_404(Organization, codename=codename)
    
    # Load the Company Profile for the user's Active Space
    space = request.user.get_profile().space
    context['space'] = space
    company = CompanyProfile.objects.get(space=space, organization=organization)
    context['company'] = company

    context['BING_MAPS_KEY'] = settings.BING_MAPS_KEY

    # check the user is a member of the space this organization belongs to
    if not request.user in space.members:
        raise PermissionDenied

    # add whether the user is a company editor to the context
    context['is_user_editor'] = organization.is_editor(request.user)

    # extract user email domain
    # this is used by the 'Invite Colleague' feature
    context['domain'] = request.user.email.split('@')[1]

    # Authentication is Token-based
    headers = {
        'referer': settings.API_HOST,
        'content-type': 'application/json',
        # use the logged-in user authorization token
        'authorization': 'Token {}'.format(request.user.get_profile().token)
    }

    # Load company Notices
    url = "{}/notices".format(settings.API_HOST)
    params = {
        'company': organization.codename
    }
    response = requests.get(url, verify=False, headers=headers, params=params)

    # This is the list displayed on the RHS
    context['staff'] = organization.members.all()[:4]

    # Latest notices (x2)
    # This is the list displayed on the RHS
    context['notices'] = []
    for notice in json.loads(response.text)['results'][:2]:
        # only display first 255 characters
        subject = strip_tags(notice['subject'])
        notice['subject'] = subject
        if len(subject) > 255:
            notice['subject'] = subject[:252] + '...'
        context['notices'].append(notice)

    # load template
    t = loader.get_template('nirit/company_profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def staff(request, codename):
    """
    Company staff page.
    Same permissions as the company home page.

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    organization = get_object_or_404(Organization, codename=codename)
    context = {}
    
    # Load the Company Profile for the user's Active Space
    space = request.user.get_profile().space
    context['space'] = space
    company = CompanyProfile.objects.get(space=space, organization=organization)
    context['company'] = company
    context['staff'] = organization.members.all()

    context['BING_MAPS_KEY'] = settings.BING_MAPS_KEY
    
    # check the user is a member of the space this organization belongs to
    if not request.user in space.members:
        raise PermissionDenied

    # Authentication is Token-based
    headers = {
        'referer': settings.API_HOST,
        'content-type': 'application/json',
        # use the logged-in user authorization token
        'authorization': 'Token {}'.format(request.user.get_profile().token)
    }

    # Load company Notices
    url = "{}/notices".format(settings.API_HOST)
    params = {
        'company': organization.codename
    }
    response = requests.get(url, verify=False, headers=headers, params=params)

    # Add statistics
    context['stats'] = {
        'members': organization.members.all(),
        'notices': json.loads(response.text),
        'expertise': organization.expertise.all()
    }

    # Add user Ownership and Editorial rights
    context['is_owner'] = organization.is_owner(request.user)
    context['is_editor'] = organization.is_editor(request.user)

    # load template
    t = loader.get_template('nirit/company_profile_staff.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def board(request, codename):
    """
    Company board page.
    Same permissions as the company home page.

    """
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    organization = get_object_or_404(Organization, codename=codename)
    context = {}

    # Load the Company Profile for the user's Active Space
    space = request.user.get_profile().space
    context['space'] = space
    company = CompanyProfile.objects.get(space=space, organization=organization)
    context['company'] = company
    context['staff'] = organization.members.all()

    context['BING_MAPS_KEY'] = settings.BING_MAPS_KEY

    # check the user is a member of the space this organization belongs to
    if not request.user in space.members:
        raise PermissionDenied

    # Authentication is Token-based
    headers = {
        'referer': settings.API_HOST,
        'content-type': 'application/json',
        # use the logged-in user authorization token
        'authorization': 'Token {}'.format(request.user.get_profile().token)
    }

    # Make an OPTIONS request to retrieve the full list of Notices for this user
    cookies = {
        'csrftoken': request.COOKIES['csrftoken'],
        'sessionid': request.COOKIES['sessionid']
    }
    url = "https://{}/api/notices".format(request.META['HTTP_HOST'])
    r = requests.options(url, verify=False, cookies=cookies)
    try:
        context['notices'] = json.dumps(json.loads(r.text)['results']['notices'])
    except:
        context['notices'] = '{}'

    # Load company Notices
    params = {
        'company': organization.codename
    }
    response = requests.get(url, verify=False, headers=headers, params=params)
    context['data'] = response.text

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
def edit_profile(request, codename):
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

    # active space
    space = request.user.get_profile().space
    context['space'] = space

    # user is allowed to edit the company
    # add the Organization form
    profile = CompanyProfile.objects.get(space=space, organization=organization)
    initial = {
        'building': profile.building,
        'floor': profile.floor,
        'directions': profile.directions
    } # initial company profile data, used is both bound and unbound forms
    if request.method == 'POST':
        # do NOT handle files in this form, as they are being uploaded via AJAX
        form = CompanyForm(request.POST, instance=organization, initial=initial)
        if form.is_valid():
            # save the model directly,
            # to avoid re-submitting the file (which would be empty at this point)
            # we do this to avoid creating the file twice
            form.instance.description = form.cleaned_data['description']
            form.instance.founded = form.cleaned_data['founded']
            form.instance.expertise = form.cleaned_data['expertise']
            form.instance.department = form.cleaned_data['department']
            form.instance.size = form.cleaned_data['size']
            # handle AJAX image uploads;
            # if a new file was uploaded, we use this one;
            # otherwise, when a logo is already assigned to the field,
            # we re-assign the existing value. Without doing this, the value would be cleared
            if request.POST.has_key('logo') and request.POST['logo']:
                form.instance.logo = request.POST['logo'].split(settings.MEDIA_URL)[1]
            elif form.instance.logo:
                form.instance.logo = form.cleaned_data['logo']
            if request.POST.has_key('square_logo') and request.POST['square_logo']:
                form.instance.square_logo = request.POST['square_logo'].split(settings.MEDIA_URL)[1]
            elif form.instance.square_logo:
                form.instance.square_logo = form.cleaned_data['square_logo']
            form.instance.save()
            # save profile data
            profile.building = form.cleaned_data['building']
            profile.floor = form.cleaned_data['floor']
            profile.directions = form.cleaned_data['directions']
            profile.save()
            # all done, redirect to company page
            destination = '/company/{}/{}'.format(organization.slug, organization.codename)
            return HttpResponseRedirect(destination)
    else:
        form = CompanyForm(instance=organization, initial=initial)
    context['form'] = form

    # load template
    t = loader.get_template('nirit/company_profile_edit.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def contact(request, codename):
    if request.method == 'GET':
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Method Not Allowed.'
        }), mimetype="application/json")

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    try:
        company = Organization.objects.get(codename=codename)
        if request.POST.has_key('subject') and request.POST['subject']:
            subject = 'A member has contacted you'
            text_content = Message().get('email_company_contact_text', {
                'name': request.user.get_profile().name,
                'company': company.name,
                'link': '{}/member/{}'.format(settings.HOST, request.user.get_profile().codename),
                'subject': request.POST['subject']
            })
            html_content = Message().get('email_company_contact_html', {
                'name': request.user.get_profile().name,
                'company': company.name,
                'link': '{}/member/{}'.format(settings.HOST, request.user.get_profile().codename),
                'subject': linebreaks(request.POST['subject'])
            }) 
            company.mail_editors(subject, text_content, html_content)
    except Organization.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({
            'status': '404',
            'reason': 'Unknown Company.'
        }), mimetype="application/json")

    response = HttpResponse(json.dumps({
        'status': '200',
        'data': {
            'subject': request.POST['subject'] if request.POST.has_key('subject') else '',
            'company': codename
        }
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


@login_required
def invite_staff(request, codename):
    """
    Invite staff to join Company.
    Available through AJAX. POST only allowed.

    """
    if request.method == 'GET':
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Method Not Allowed.'
        }), mimetype="application/json")

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    try:
        company = Organization.objects.get(codename=codename)
        if request.POST.has_key('list') and request.POST['list']:
            # emails can be separated by whitespaces, commas or semi-colons
            cleaned_list = re.sub(r'[,;\s]', ' ', request.POST['list']).split()
            recipients_list = []
            for recipient in cleaned_list:
                try:
                    validate_email(recipient)
                except:
                    # skip invalid email addresses
                    continue
                match = utils.lookup_email(recipient)
                if not match or match != company:
                    # skip non-company emails,
                    # or emails from a different company
                    continue
                recipients_list.append(recipient)
            if recipients_list:
                subject = 'You are invited to join Nirit'
                c = {
                    'name': request.user.get_profile().name,
                    'company': company.name,
                    'link': '{}/member/sign-up'.format(settings.HOST),
                }
                text_content = Message().get('email_invite_members_text', c)
                html_content = Message().get('email_invite_members_html', c)
                from_email = settings.EMAIL_FROM
                msg = EmailMultiAlternatives(subject, text_content, from_email, recipients_list)
                if html_content:
                    msg.attach_alternative(html_content, "text/html")
                msg.send()
    except Organization.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({
            'status': '404',
            'reason': 'Unknown Company.'
        }), mimetype="application/json")

    response = HttpResponse(json.dumps({
        'status': '200',
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


@login_required
def invite_company(request, codename):
    """
    Invite Company to join Space.
    Available through AJAX. POST only allowed.

    """
    if request.method == 'GET':
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Method Not Allowed.'
        }), mimetype="application/json")

    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check email address is valid
    try:
        email = request.POST['email']
        validate_email(email)
    except Exception:
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Enter a valid email address.'
        }), mimetype="application/json")

    # Create a token for the space,
    # and assign it the email address
    token = OToken()
    token.space = request.user.get_profile().space
    token.email = email
    token.save()

    onwer_profile = request.user.get_profile()
    subject = 'You are invited to join Nirit'
    c = {
        'name': onwer_profile.name,
        'company': onwer_profile.company.name,
        'link': '{}/member/sign-up/join?token={}'.format(settings.HOST, token.key),
    }
    text_content = Message().get('email_invite_company_text', c)
    html_content = Message().get('email_invite_company_html', c)
    from_email = settings.EMAIL_FROM
    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    if html_content:
        msg.attach_alternative(html_content, "text/html")
    msg.send()

    response = HttpResponse(json.dumps({
        'status': '200',
        'token': token.key
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response
