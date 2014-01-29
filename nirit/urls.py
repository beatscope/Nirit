# nirit/urls.py
import logging
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from filebrowser.sites import site as filebrowser_site
from nirit.admin import site
from nirit.models import Page
from nirit.forms import PassResetForm
from nirit.uploads import FileUploader

# Static pages regular expression
pages_regex = r'^(?P<page>{})$'.format('|'.join([p['slug'] for p in Page.objects.filter(status=True).values('slug')]))

urlpatterns = patterns('',

    # Public
    url(r'^$', 'nirit.views_public.landing'),
    url(r'^sitemap.xml', 'nirit.views_public.sitemap'),
    url(pages_regex, 'nirit.views_public.page'),
    url(r'^spaces/$', 'nirit.views_public.spaces'),
    url(r'^supplier/(?P<slug>.+)/$', 'nirit.views_public.supplier'),
    url(r'^action/register-interest/$', 'nirit.views_public.action', {'action': 'register-interest'}),

    url(r'^board/[\w-]*/(?P<codename>\w+)/', 'nirit.views.board', name='board'),
    url(r'^board/$', 'nirit.views.board'),
    url(r'^directory/[\w-]*/(?P<codename>\w+)/', 'nirit.views.directory'),
    url(r'^directory/$', 'nirit.views.directory'),
    url(r'^amenities/[\w-]*/(?P<codename>\w+)/', 'nirit.views.amenities'),
    url(r'^amenities/$', 'nirit.views.amenities'),
    url(r'^amenities/request/$', 'nirit.views.amenities_request'),
    url(r'^amenities/request-edit/$', 'nirit.views.amenities_request', {'edit': True}),

    # Sign-up
    url(r'^member/sign-up/$', 'nirit.views_signup.sign_up'),

    # Sign-up - Affiliated
    url(r'^member/sign-up/complete/$', 'nirit.views_signup.complete'),

    # Sign-up - Owners
    url(r'^member/sign-up/activation-required/$', 'nirit.views_signup.activation_required'),
    url(r'^member/sign-up/activate/$', 'nirit.views_signup.activate'),
    url(r'^member/sign-up/join/$', 'nirit.views_signup.join'),

    # Sign-up - Unaffiliated
    url(r'^member/sign-up/registration-complete/$', 'nirit.views_signup.registration_complete'),
    url(r'^member/activate/(?P<activation_key>\w+)/$', 'nirit.views_signup.registration_activate'),

    # Member
    url(r'^member/password/reset/$', 'django.contrib.auth.views.password_reset',
        {
            'from_email': settings.EMAIL_FROM,
            'password_reset_form': PassResetForm,
            'post_reset_redirect' : '/member/password/reset/done/'
        },
        name="password_reset"),
    url(r'^member/password/reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    url(r'^member/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', 
        {
            'post_reset_redirect' : '/member/password/reset/complete/'
        }),
    url(r'^member/password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete'),
    url(r'^member/password/change/', 'django.contrib.auth.views.password_change',
        {
            'post_change_redirect': '/'
        }),
    url(r'^member/set-preference/(?P<setting>\w+)/(?P<value>\w+)/$', 'nirit.views_member.set_preference'),
    url(r'^member/account/edit/$', 'nirit.views_member.edit_profile'),
    url(r'^member/account/$', 'nirit.views_member.profile'),
    url(r'^member/(?P<codename>.+)/$', 'nirit.views_member.profile'),
    url(r'^member/$', 'nirit.views_member.profile'),
    url(r'^logout', 'django.contrib.auth.views.logout_then_login'),

    # Company
    url(r'^company/[\w-]*/(?P<codename>\w+)/board/$', 'nirit.views_company.board'),
    url(r'^company/[\w-]*/(?P<codename>\w+)/edit/$', 'nirit.views_company.edit_profile'),
    url(r'^company/[\w-]*/(?P<codename>\w+)/staff/$', 'nirit.views_company.staff'),
    url(r'^company/[\w-]*/(?P<codename>\w+)/$', 'nirit.views_company.profile'),
    url(r'^company$', 'nirit.views_company.profile'),

    # AJAX Interfaces
    url(r'^upload$', login_required(FileUploader())),
    url(r'^contact/member/(?P<codename>.+)$', 'nirit.views_member.contact'),
    url(r'^approval/member/(?P<codename>.+)/(?P<action>\w+)$', 'nirit.views_member.set_status'),
    url(r'^contact/company/(?P<codename>\w+)$', 'nirit.views_company.contact'),
    url(r'^invite/members/(?P<codename>\w+)$', 'nirit.views_company.invite_staff'),
    url(r'^invite/company/(?P<codename>\w+)$', 'nirit.views_company.invite_company'),
    url(r'^approval/company/(?P<codename>\w+)/(?P<action>\w+)$', 'nirit.views_company.set_status'),

    # Admin
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^back-office/', include(site.urls)),
    url(r'^back-office/filebrowser/', include(filebrowser_site.urls)),
    url(r'^markitup/', include('markitup.urls'))

)
