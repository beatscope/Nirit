# nirit/views_signup.py
import logging
import json
import requests
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.contrib.auth import login as auth_login
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.utils.encoding import force_unicode
from django.conf import settings
from nirit.models import Notice, OToken, CompanyProfile
from nirit.forms import CompanyForm, SignUpForm
from nirit.fixtures import Message

logger = logging.getLogger('nirit.signup')


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

def complete(request):
    t = loader.get_template('registration/sign_up_complete.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))

def activation_required(request):
    t = loader.get_template('registration/sign_up_activation_required.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))

def activate(request):
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

                        # Notify Managers and Admins
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

