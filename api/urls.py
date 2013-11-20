# nirit/urls_api.py
from django.conf.urls.defaults import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns
from api.views import BuildingListView, BuildingView, \
                      NoticeListView, NoticeView, NoticePostView, \
                      OrganizationListView, OrganizationView, \
                      ExpertiseListView, ExpertiseView, ExpertiseCreateView, \
                      SupplierListView

urlpatterns = patterns('',

    url(r'^$', 'api.views.api_root'),
    url(r'^buildings/$', BuildingListView.as_view(), name='buildings-list'),
    url(r'^buildings/(?P<codename>\w+)/$', BuildingView.as_view(), name='building-detail'),
    url(r'^notices/post$', NoticePostView.as_view(), name='notice-add'),
    url(r'^notices/$', NoticeListView.as_view(), name='notices-list'),
    url(r'^notices/(?P<pk>[0-9]+)/$', NoticeView.as_view(), name='notice-detail'),
    url(r'^organizations/$', OrganizationListView.as_view(), name='organizations-list'),
    url(r'^organizations/(?P<codename>\w+)/$', OrganizationView.as_view(), name='organization-detail'),
    url(r'^expertise/add$', ExpertiseCreateView.as_view(), name='expertise-add'),
    url(r'^expertise/$', ExpertiseListView.as_view(), name='expertise-list'),
    url(r'^expertise/(?P<pk>[0-9]+)/$', ExpertiseView.as_view(), name='expertise-detail'),
    url(r'^suppliers/$', SupplierListView.as_view(), name='suppliers-list'),

    # include login URLs for the browseable API.
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

)

urlpatterns = format_suffix_patterns(urlpatterns)
