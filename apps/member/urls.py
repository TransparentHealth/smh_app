# Copyright Videntity Systems, Inc.
from django.conf.urls import url

from .views import (
    approve_resource_request, revoke_resource_request,
    CreateMemberView, DashboardView, DataSourcesView, DeleteMemberView, RecordsView,
    UpdateMemberView
)

# Copyright Videntity Systems Inc.

app_name = 'member'
urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/records/(?P<resource_name>[\w-]+)/$',
        RecordsView.as_view(),
        name='records'),
    url(r'^(?P<pk>[0-9]+)/data-sources/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^(?P<pk>[0-9]+)/data-sources/(?P<resource_name>[\w]+)/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^(?P<pk>[0-9]+)/data-sources/(?P<resource_name>[\w]+)/(?P<record_type>[\w]+)/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^new/$',
        CreateMemberView.as_view(),
        name='member-create'),
    url(r'^(?P<pk>[0-9]+)/$',
        UpdateMemberView.as_view(),
        name='member-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
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
]
