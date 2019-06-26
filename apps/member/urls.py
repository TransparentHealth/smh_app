# Copyright Videntity Systems, Inc.
from django.conf.urls import url

from .views import (
    approve_resource_request, revoke_resource_request, resource_request_response,
    CreateMemberView, DeleteMemberView, UpdateMemberView,
    DashboardView, DataSourcesView, RecordsView, OrganizationsView,
    SummaryView, ProvidersView,
    NotificationsView,
)

# Copyright Videntity Systems Inc.

app_name = 'member'
urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/summary/$',
        SummaryView.as_view(),
        name='summary'),
    url(r'^(?P<pk>[0-9]+)/records/(?P<resource_name>[\w-]+)?/?$',
        RecordsView.as_view(),
        name='records'),
    url(r'^(?P<pk>[0-9]+)/providers/$',
        ProvidersView.as_view(),
        name='providers'),
    url(r'^(?P<pk>[0-9]+)/data-sources/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^(?P<pk>[0-9]+)/data-sources/(?P<resource_name>[\w]+)/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^(?P<pk>[0-9]+)/data-sources/(?P<resource_name>[\w]+)/(?P<record_type>[\w]+)/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^(?P<pk>[0-9]+)/organizations/$',
        OrganizationsView.as_view(),
        name='organizations'),
    url(r'^new/$',
        CreateMemberView.as_view(),
        name='member-create'),
    url(r'^(?P<pk>[0-9]+)/$',
        UpdateMemberView.as_view(),
        name='member-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        DeleteMemberView.as_view(),
        name='member-delete'),
    url(r'^notifications/$',
        NotificationsView.as_view(),
        name='notifications'),
    url(r'^$',
        DashboardView.as_view(), name='dashboard'),

    # Member/Org ResourceRequests
    url(r'^resource_request_response/$', resource_request_response, name='resource_request_response'),
    url(r'^approve_resource_request/(?P<pk>[0-9]+)/$',
        approve_resource_request,
        name='approve_resource_request'),
    url(r'^revoke_resource_request/(?P<pk>[0-9]+)/$',
        revoke_resource_request,
        name='revoke_resource_request'),
]
