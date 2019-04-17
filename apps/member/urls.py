# Copyright Videntity Systems, Inc.
from django.conf.urls import url

from .views import (
    RecordsView, DataSourcesView, CreateMemberView, MemberDetailView, DeleteMemberView,
    DashboardView, approve_resource_request, get_member_data, revoke_resource_request
)

# Copyright Videntity Systems Inc.

app_name = 'member'
urlpatterns = [
    url(r'^(?P<pk>\d)/records/$',
        RecordsView.as_view(),
        name='records'),
    url(r'^(?P<pk>\d)/data-sources/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^new/$',
        CreateMemberView.as_view(),
        name='member-create'),
    url(r'^(?P<pk>\d)/$',
        MemberDetailView.as_view(),
        name='member-detail'),
    url(r'^(?P<pk>\d)/delete/$',
        DeleteMemberView.as_view(),
        name='member-delete'),
    url(r'^$',
        DashboardView.as_view(), name='dashboard'),
    url(r'^approve_resource_request/(?P<pk>[0-9]+)/$',
        approve_resource_request,
        name='approve_resource_request'),
    url(r'^revoke_resource_request/(?P<pk>[0-9]+)/$',
        revoke_resource_request,
        name='revoke_resource_request'),
    url(r'^(?P<pk>[0-9]+)/get_data/(?P<resource_name>[\w]+)/(?P<record_type>[\w]+)/$',
        get_member_data,
        name='get_member_data'),
]
