# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import (
    org_create_member_view,
    DashboardView, CreateOrganizationView, DeleteOrganizationView, UpdateOrganizationView,
)


# Copyright Videntity Systems Inc.

app_name = 'org'
urlpatterns = [
    url(r'^dashboard$',
        DashboardView.as_view(),
        name='dashboard'),
    url(r'^organization/(?P<pk>[0-9]+)/$',
        UpdateOrganizationView.as_view(),
        name='organization-update'),
    url(r'^organization/new/$',
        CreateOrganizationView.as_view(),
        name='organization-add'),
    url(r'^organization/(?P<pk>[0-9]+)/delete/$',
        DeleteOrganizationView.as_view(),
        name='organization-delete'),
    url(r'(?P<org_slug>[-\w]+)/create_member/create',
        org_create_member_view,
        name='org_create_member',)
]
