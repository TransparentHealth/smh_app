# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import (
    DashboardView, CreateOrganizationView, DeleteOrganizationView, UpdateOrganizationView,
    LocalUserAPI, SearchView
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
    url(r'^org-member-api$',
        LocalUserAPI.as_view(),
        name='org-member-api'),
    url(r'^search$',
        SearchView.as_view(),
        name='search'),

]
