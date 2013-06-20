# nirit/urls.py
from django.conf.urls.defaults import patterns, include, url
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import databrowse
import nirit.admin

urlpatterns = patterns('',

    # Pages
    url(r'^$', 'nirit.views.landing'),
    url(r'^user/account', 'nirit.views.user_account'),
    url(r'^board/[\w-]*/(?P<codename>\w+)', 'nirit.views.board'),
    url(r'^directory/[\w-]*/(?P<codename>\w+)', 'nirit.views.directory'),
    url(r'^company/[\w-]*/(?P<codename>\w+)', 'nirit.views.company'),

    # REST API 
    url(r'^notices$', 'nirit.views.notices'),
    url(r'^notices/(?P<object_code>[\d\w]+)/?(?P<action>\w+)?/?(?P<start>\d+)?$', 'nirit.views.notices'),

    # Admin
    url(r'^browse/(.*)', user_passes_test(lambda u: u.is_superuser)(databrowse.site.root)),

    # Accounts
    url(r'^logout', 'django.contrib.auth.views.logout_then_login'),

    url(r'^user/password/reset/$',
        'django.contrib.auth.views.password_reset',
        {'post_reset_redirect' : '/user/password/reset/done/'},
        name="password_reset"),
    url(r'^user/password/reset/done/$',
        'django.contrib.auth.views.password_reset_done'),
    url(r'^user/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        'django.contrib.auth.views.password_reset_confirm', 
        {'post_reset_redirect' : '/user/password/reset/complete/'}),
    url(r'^user/password/reset/complete/$', 
        'django.contrib.auth.views.password_reset_complete'),

    url(r'^user/password/change',
        'django.contrib.auth.views.password_change',
        {'post_change_redirect': '/'}),

)
