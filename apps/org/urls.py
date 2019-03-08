# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import (
    DashboardView, CreateOrganizationView, DeleteOrganizationView, UpdateOrganizationView
)


# Copyright Videntity Systems Inc.

app_name = 'org'
urlpatterns = [
    url(r'^dashboard$',
        DashboardView.as_view(),
        name='dashboard'),
    url(r'^organization/(?P<pk>\d)/$',
        UpdateOrganizationView.as_view(),
        name='organization-update'),
    url(r'^organization/new/$',
        CreateOrganizationView.as_view(),
        name='organization-add'),
    url(r'^organization/(?P<pk>\d)/delete/$',
        DeleteOrganizationView.as_view(),
        name='organization-delete'),
]
