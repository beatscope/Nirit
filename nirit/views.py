# nirit/views.py
import logging
import json
import operator
import re
import requests
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.core.validators import validate_email
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.template import RequestContext, loader
from django.utils.encoding import force_unicode
from django.utils.html import strip_tags, linebreaks
from django.conf import settings
from nirit.models import Page, Space, Notice, Organization, \
                         OToken, UserProfile, CompanyProfile, Supplier
from nirit.manager import ModelManager
from nirit.forms import CompanyForm, MemberForm, UserForm, SignUpForm
from nirit.fixtures import Message
from nirit import utils

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
    else:
        # Redirect authenticated user to their primary space's Notice Board
        destination = 'board/{}'.format(request.user.get_profile().space.link)
        return HttpResponseRedirect(destination)

    t = loader.get_template('nirit/index.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


def page(request, page):
    p = get_object_or_404(Page, slug=page)
    t = loader.get_template('nirit/page.html')
    c = RequestContext(request, {
        'title': p.title,
        'body': p.body
    })
    return HttpResponse(t.render(c))


def sign_up(request):
    explanation = ''
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Generate user hash/slug
            user.get_profile().generate_hash()
            # Handle user role
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
                # Make sure this token is assigned to a user
                user = t.user
                if not user:
                    raise PermissionDenied

                # Log the user in
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user)

                context['status'] = 'ACTIVATED'

                # This is the one-time chance for the user to create a company
                # The Company creation form is a slimmed-down versio of the Company Edit form
                # (only required information is desplayed, so that the same form class can be used)
                if request.method == 'POST':
                    form = CompanyForm(request.POST)
                    if form.is_valid():
                        data = form.save()
                        company = data['organization']
                        floor = data['floor']
                        directions = data['directions']

                        # Create a Company Profile on this space
                        CompanyProfile.objects.create(organization=company,
                                                      space=t.space,
                                                      floor=floor,
                                                      directions=directions)

                        # Assign user to the company
                        profile = user.get_profile()
                        profile.company = company
                        profile.save()

                        # Flag token as redeemed 
                        t.redeemed = True
                        t.save()

                        # Post INTRO notice to board
                        # verification is token-based
                        token = profile.token
                        headers = {
                            'referer': settings.API_HOST,
                            'content-type': 'application/json',
                            'authorization': 'Token {}'.format(token)
                        }
                        data = {
                            'subject': u'{} has just joined Nirit'.format(company.name),
                            'body': force_unicode(company.description),
                            'spaces': [t.space.codename],
                            'type': '{}'.format(Notice.INTRO),
                            'official': 'on'
                        }
                        url = "{}/notices/post".format(settings.API_HOST)
                        r = requests.post(url, verify=False, headers=headers, data=json.dumps(data))

                        # Notify Space Managers and Admins
                        subject = 'A new Company has just joined Nirit'
                        data = {
                            'name': company.name,
                            'link': '{}/member/account'.format(settings.HOST)
                        }
                        text_content = Message().get('email_new_company_text', data)
                        html_content = Message().get('email_new_company_html', data)
                        mail_admins(subject, text_content, html_message=html_content)
                        t.space.mail_managers(subject, text_content, html_content)

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
def user_profile(request, codename=None):
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
    #   - for Space Managers
    #   - only on member's own page
    if profile.user == request.user:
        if profile.space and 'Space Manager' in profile.roles:
            context['companies_awaiting'] = profile.space.get_pending_companies()

    t = loader.get_template('nirit/user_profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def user_set_status(request, codename, action):
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


def sitemap(request):
    suppliers = Supplier.objects.all()
    t = loader.get_template('sitemap.xml')
    c = RequestContext(request, {
        'host': settings.HOST,
        'suppliers': suppliers,
    })
    return HttpResponse(t.render(c), mimetype="text/xml")


@login_required
def company_set_status(request, codename, action):
    # Check the user is active
    if not request.user.get_profile().status == UserProfile.VERIFIED:
        raise PermissionDenied

    # Check the user is a Space Manager
    if not 'Space Manager' in request.user.get_profile().roles:
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
def company(request, codename=None):
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
def company_staff(request, codename):
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
def company_board(request, codename):
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
    profile = CompanyProfile.objects.get(space=request.user.get_profile().space, organization=organization)
    initial = {
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
            if request.POST.has_key('image') and request.POST['image']:
                form.instance.image = request.POST['image'].split(settings.MEDIA_URL)[1]
            elif form.instance.image:
                form.instance.image = form.cleaned_data['image']
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
def contact_company(request, codename):
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
def invite_members(request, codename):
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
def contact_member(request, codename):
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
