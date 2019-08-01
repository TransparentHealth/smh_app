# Copyright Videntity Systems, Inc.
from django.conf.urls import url

from .views import (
    approve_resource_request, revoke_resource_request, resource_request_response,
    CreateMemberView, DeleteMemberView, UpdateMemberView,
    DashboardView, DataSourcesView, RecordsView, DataView,
    PrescriptionDetailModalView,
    OrganizationsView,
    SummaryView, ProvidersView, NotificationsView,
    RequestAccessView,
    redirect_subject_url_to_member,
)

# Copyright Videntity Systems Inc.

app_name = 'member'
urlpatterns = [
    # A member url with a 15-digit id is interpreted as a subject_id,
    # redirected to a url below
    url(r'^(?P<subject>[0-9]{15})/$',
        redirect_subject_url_to_member,
        name='subject_url'),
    url(r'^(?P<subject>[0-9]{15})/(?P<rest>.*)$',
        redirect_subject_url_to_member),

    # Member urls (using pk)
    url(r'^(?P<pk>[0-9]+)/summary/$',
        SummaryView.as_view(),
        name='summary'),
    url(r'^(?P<pk>[0-9]+)/records/(?P<resource_name>[\w-]+)?/?$',
        RecordsView.as_view(),
        name='records'),

    # JSON to medical data
    url(r'^(?P<pk>[0-9]+)/data/(?P<resource_type>[\w-]+)/(?P<resource_id>[\w-]+)$',
        DataView.as_view(),
        name='data'),

    # modal HTML content
    url(r'^(?P<pk>[0-9]+)/modal/prescription/(?P<resource_id>[\w-]+)$',
        PrescriptionDetailModalView.as_view(),
        name='prescription-modal'),

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
    url(r'^(?P<pk>[0-9]+)/request-access/$',
        RequestAccessView.as_view(),
        name='request-access'),
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
    url(r'^resource_request_response/$', resource_request_response,
        name='resource_request_response'),
    url(r'^approve_resource_request/(?P<pk>[0-9]+)/$',
        approve_resource_request,
        name='approve_resource_request'),
    url(r'^revoke_resource_request/(?P<pk>[0-9]+)/$',
        revoke_resource_request,
        name='revoke_resource_request'),
]
