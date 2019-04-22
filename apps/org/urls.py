# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import (
    org_create_member_additional_info_view,
    DashboardView, CreateOrganizationView, DeleteOrganizationView, OrgCreateMemberView,
    OrgCreateMemberBasicInfoView, OrgCreateMemberVerifyIdentityView, UpdateOrganizationView,
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

    # URLs for the process of having a User at an Organization create a new Member
    url(r'(?P<org_slug>[-\w]+)/create_member/create',
        OrgCreateMemberView.as_view(),
        name='org_create_member'),
    url(r'(?P<org_slug>[-\w]+)/create_member/(?P<username>[-\w]+)/basic_info',
        OrgCreateMemberBasicInfoView.as_view(),
        name='org_create_member_basic_info'),
    url(r'(?P<org_slug>[-\w]+)/create_member/(?P<username>[-\w]+)/verify_identity',
        OrgCreateMemberVerifyIdentityView.as_view(),
        name='org_create_member_verify_identity'),
    url(r'(?P<org_slug>[-\w]+)/create_member/(?P<username>[-\w]+)/additional_info',
        org_create_member_additional_info_view,
        name='org_create_member_additional_info'),
]
