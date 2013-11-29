# nirit/views_member.py
import logging
import json
import re
import requests
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.template import RequestContext, loader
from django.utils.html import linebreaks
from django.conf import settings
from nirit.models import Notice, Organization, UserProfile
from nirit.manager import ModelManager
from nirit.forms import MemberForm, UserForm
from nirit.fixtures import Message

logger = logging.getLogger('nirit.member')


@login_required
@ensure_csrf_cookie
def profile(request, codename=None):
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check member being viewed
    # logged-in user or other?
    if codename:
        try:
            profile = UserProfile.objects.get(codename=codename)
        except UserProfile.DoesNotExist:
            raise Http404
    else:
        profile = request.user.get_profile()

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
        notices = json.dumps(json.loads(r.text)['results']['notices'])
    except:
        notices = '{}'

    # Load user's Notices
    params = {
        'member': profile.codename
    }
    response = requests.get(url, verify=False, headers=headers, params=params)
    context = {
        'member': profile,
        'data': response.text,
        'notices': notices
    }

    # Add companies approval
    #   - for Managers
    #   - only on member's own page
    context['is_manager'] = False
    if profile.user == request.user:
        if profile.space and 'Manager' in profile.roles:
            context['is_manager'] = True
            context['companies_awaiting'] = profile.space.get_pending_companies()

    t = loader.get_template('nirit/user_profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def set_status(request, codename, action):
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check the user is an Editor
    if not request.user.get_profile().company.is_editor(request.user):
        raise PermissionDenied

    # Check action
    if action not in ('activate', 'ban', 'assign', 'revoke'):
        return HttpResponseBadRequest(json.dumps({
            'status': '400',
            'reason': 'Unknown Action.'
        }), mimetype="application/json")

    try:
        profile = UserProfile.objects.get(codename=codename)
        if action == 'activate':
            profile.status = UserProfile.VERIFIED
            profile.save()
            # email user
            subject = 'Your membership has been approved'
            text_content = Message().get('email_sign_up_activated_text', {
                'first_name': profile.name,
                'link': '{}/member/{}'.format(settings.HOST, profile.codename)
            })
            html_content = Message().get('email_sign_up_activated_html', {
                'first_name': profile.name,
                'link': '{}/member/{}'.format(settings.HOST, profile.codename)
            })
            profile.mail(subject, text_content, html_content)
        elif action == 'ban':
            profile.status = UserProfile.BANNED
            profile.save()
        elif action == 'assign':
            profile.user.groups.remove(Group.objects.get(name='Staff'))
            profile.user.groups.add(Group.objects.get(name='Rep'))
        elif action == 'revoke':
            profile.user.groups.remove(Group.objects.get(name='Rep'))
            profile.user.groups.add(Group.objects.get(name='Staff'))
    except UserProfile.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({
            'status': '404',
            'reason': 'Unknown User.'
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
def edit_profile(request):
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
                # handle AJAX image uploads;
                # if a new file was uploaded, we use this one;
                # otherwise, when an image is already assigned to the field,
                # we re-assign the existing value. Without doing this, the value would be cleared
                if request.POST.has_key('thumbnail') and request.POST['thumbnail']:
                    member_form.instance.thumbnail = request.POST['thumbnail'].split(settings.MEDIA_URL)[1]
                elif member_form.instance.thumbnail:
                    member_form.instance.thumbnail = member_form.cleaned_data['thumbnail']
                # save the instance
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
        'member': request.user.get_profile(),
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
        profile = UserProfile.objects.get(codename=codename)
        if request.POST.has_key('subject') and request.POST['subject']:
            subject = 'A member has contacted you'
            text_content = Message().get('email_member_contact_text', {
                'name': request.user.get_profile().name,
                'company': request.user.get_profile().company.name,
                'link': '{}/member/{}'.format(settings.HOST, request.user.get_profile().codename),
                'subject': request.POST['subject']
            })
            html_content = Message().get('email_member_contact_html', {
                'name': request.user.get_profile().name,
                'company': request.user.get_profile().company.name,
                'link': '{}/member/{}'.format(settings.HOST, request.user.get_profile().codename),
                'subject': linebreaks(request.POST['subject'])
            }) 
            from_email = settings.EMAIL_FROM
            recipients_list = [profile.user.email]
            if recipients_list:
                msg = EmailMultiAlternatives(subject, text_content, from_email, recipients_list)
                if html_content:
                    msg.attach_alternative(html_content, "text/html")
                msg.send()
    except UserProfile.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({
            'status': '404',
            'reason': 'Unknown Member.'
        }), mimetype="application/json")

    response = HttpResponse(json.dumps({
        'status': '200',
        'data': {
            'subject': request.POST['subject'] if request.POST.has_key('subject') else '',
            'member': codename
        }
    }), mimetype="application/json")
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response
