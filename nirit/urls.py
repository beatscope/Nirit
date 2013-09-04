# nirit/urls.py
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from nirit.admin import site
from nirit.forms import PassResetForm
from nirit.uploads import FileUploader

urlpatterns = patterns('',

    # Pages
    url(r'^$', 'nirit.views.landing'),
    url(r'^board/[\w-]*/(?P<codename>\w+)', 'nirit.views.board'),
    url(r'^directory/[\w-]*/(?P<codename>\w+)', 'nirit.views.directory'),
    url(r'^api/companies/(?P<codename>\w+)/(?P<group>\w+)', 'nirit.views.company_api'),

    # Member pages
    url(r'^member/sign-up$', 'nirit.views.sign_up'),
    url(r'^member/sign-up/complete$', 'nirit.views.sign_up_complete'),
    url(r'^member/sign-up/activation-required$', 'nirit.views.sign_up_activation_required'),
    url(r'^member/sign-up/activate$', 'nirit.views.sign_up_activate'),

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
    url(r'^member/password/change', 'django.contrib.auth.views.password_change',
        {
            'post_change_redirect': '/'
        }),

    url(r'^member/set-preference/(?P<setting>\w+)/(?P<value>\w+)$', 'nirit.views.set_preference'),
    url(r'^member/account/edit$', 'nirit.views.user_profile_edit'),
    url(r'^member/account$', 'nirit.views.user_profile'),
    url(r'^member/(?P<username>.*)/(?P<action>\w+)$', 'nirit.views.user_set_status'),
    url(r'^member/(?P<username>.*)$', 'nirit.views.user_profile'),
    url(r'^logout', 'django.contrib.auth.views.logout_then_login'),

    # Company Pages
    url(r'^company/(?P<codename>\w+)/(?P<action>\w+)$', 'nirit.views.company_set_status'),
    url(r'^company/[\w-]*/(?P<codename>\w+)/board$', 'nirit.views.company_board'),
    url(r'^company/[\w-]*/(?P<codename>\w+)/edit$', 'nirit.views.company_edit'),
    url(r'^company/[\w-]*/(?P<codename>\w+)/staff$', 'nirit.views.company_staff'),
    url(r'^company/[\w-]*/(?P<codename>\w+)$', 'nirit.views.company'),

    # Upload AJAX Interface
    url(r'^upload$', login_required(FileUploader())),

    # Admin
    url(r'^back-office', include(site.urls)),

)
