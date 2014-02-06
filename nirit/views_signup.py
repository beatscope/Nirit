# nirit/views_signup.py
import logging
import json
import re
import requests
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.contrib.auth import login as auth_login
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.utils.encoding import force_unicode
from django.conf import settings
from nirit.models import Notice, OToken, CompanyProfile, RegistrationProfile
from nirit.forms import CompanyForm, SignUpForm
from nirit.fixtures import Message

logger = logging.getLogger('nirit.signup')

SHA1_RE = re.compile('^[a-f0-9]{40}$')


def sign_up(request):
    explanation = ''
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
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
                if not settings.DEBUG:
                    html_content = Message().get('email_sign_up_success_html', data)
                else:
                    html_content = None
                company.mail_editors(subject, text_content, html_content)
                return HttpResponseRedirect('/member/sign-up/complete')
            elif user.is_active:
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
                if not settings.DEBUG:
                    html_content = Message().get('email_activation_required_html', data)
                else:
                    html_content = None
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                if html_content:
                    msg.attach_alternative(html_content, "text/html")
                msg.send()
                return HttpResponseRedirect('/member/sign-up/activation-required')
            else:
                # Unaffiliated User created.
                return HttpResponseRedirect('/member/sign-up/registration-complete')
                
    else:
        form = SignUpForm()
        explanation = Message().get('welcome')

    t = loader.get_template('registration/sign_up.html')
    c = RequestContext(request, {
        'form': form,
        'explanation': explanation
    })
    return HttpResponse(t.render(c))

def complete(request):
    """
    The registration complete page for Affiliated Members.

    """
    t = loader.get_template('registration/sign_up_complete.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))


def activation_required(request):
    """
    The registration complete page for Owners.
    Owners are required to activate their accounts.
    
    """
    t = loader.get_template('registration/sign_up_activation_required.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))


def activate(request):
    """
    Owner activation page.
    Provides the form to create a Company Profile when activated successfully.

    """
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
                context['space'] = t.space

                # This is the one-time chance for the user to create a company
                # The Company creation form is a slimmed-down version of the Company Edit form
                # (only required information is displayed, so that the same form class can be used)
                if request.method == 'POST':
                    form = CompanyForm(request.POST)
                    if form.is_valid():
                        data = form.save()
                        company = data['organization']
                        building = data['building'] if data.has_key('building') else None
                        floor = data['floor'] if data.has_key('floor') else None

                        # Create a Company Profile on this space
                        CompanyProfile.objects.create(organization=company,
                                                      space=t.space,
                                                      building=building,
                                                      floor=floor)

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

                        # Notify Managers and Admins
                        subject = 'A new Company has just joined Nirit'
                        data = {
                            'name': company.name,
                            'link': '{}/member/account'.format(settings.HOST)
                        }
                        text_content = Message().get('email_new_company_text', data)
                        if not settings.DEBUG:
                            html_content = Message().get('email_new_company_html', data)
                        else:
                            html_content = None
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


def join(request):
    """
    Handles Company (Owners) registration in one single form.
    The form requires to be sent from a manager in an existing Space.
    Failing that, the token will not exist.

    """
    form = None
    company_form = None
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
                # Make sure this token is assigned to an email address
                if not t.email:
                    context['status'] = 'FAILED'
                else:
                    # This form allows membership and company creation,
                    # in the same form
                    context['status'] = 'ACTIVATED'
                    context['space'] = t.space
                    context['explanation'] = Message().get('welcome/join')

                    # SignUp and Company Form
                    if request.method == 'POST':
                        form = SignUpForm(request.POST)
                        company_form = CompanyForm(request.POST)
                        if form.is_valid() and company_form.is_valid():
                            # Create user
                            user = form.save()

                            # Create organization
                            data = company_form.save()
                            company = data['organization']
                            building = data['building'] if data.has_key('building') else None
                            floor = data['floor'] if data.has_key('floor') else None

                            # Create a Company Profile on this space
                            CompanyProfile.objects.create(organization=company,
                                                          space=t.space,
                                                          building=building,
                                                          floor=floor)

                            # Assign user to the company and space
                            profile = user.get_profile()
                            profile.company = company
                            profile.space = t.space
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

                            # Notify Managers and Admins
                            subject = 'A new Company has just joined Nirit'
                            data = {
                                'name': company.name,
                                'link': '{}/member/account'.format(settings.HOST)
                            }
                            text_content = Message().get('email_new_company_text', data)
                            if not settings.DEBUG:
                                html_content = Message().get('email_new_company_html', data)
                            else:
                                html_content = None
                            mail_admins(subject, text_content, html_message=html_content)
                            t.space.mail_managers(subject, text_content, html_content)

                            # Finally, redirect to company page
                            destination = '/company/{}/{}'.format(company.slug, company.codename)
                            return HttpResponseRedirect(destination)
                    else:
                        form = SignUpForm(initial={'email': t.email, 'join': True})
                        company_form = CompanyForm()
    else:
        context['status'] = 'FAILED'

    if form:
        context['form'] = form
    if company_form:
        context['company_form'] = company_form
    t = loader.get_template('registration/sign_up_join.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


def registration_complete(request):
    """
    The registration complete page for Unaffiliated Members.
    Unaffiliated Members required to activate their accounts.

    """
    t = loader.get_template('registration/sign_up_registration_complete.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))


def registration_activate(request, activation_key):
    """
    Activate Unaffiliated Member, given an activation_key.

    """
    # Make sure the key we're trying conforms to the pattern of a
    # SHA1 hash; if it doesn't, no point trying to look it up in
    # the database.
    if SHA1_RE.search(activation_key):
        try:
            profile = RegistrationProfile.objects.get(activation_key=activation_key)
            activated_user = profile.activate_user(activation_key)
        except RegistrationProfile.DoesNotExist:
            pass
    t = loader.get_template('registration/sign_up_activation_complete.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))
