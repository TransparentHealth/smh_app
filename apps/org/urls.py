# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from django.urls import path
from .views import (
    CreateOrganizationView, DashboardView, DeleteOrganizationView, OrgCreateMemberView,
    OrgCreateMemberAdditionalInfoInfoView, OrgCreateMemberAlmostDoneView,
    OrgCreateMemberBasicInfoView, OrgCreateMemberCompleteView, OrgCreateMemberSuccessView,
    OrgCreateMemberVerifyIdentityView, UpdateOrganizationView, JoinOrganizationView,
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
    path('join/<slug>/<token>/',
        JoinOrganizationView.as_view(),
        name='organization-join'),

    # URLs for the process of having a User at an Organization create a new Member
    url(r'(?P<org_slug>[-\w]+)/create-member/create',
        OrgCreateMemberView.as_view(),
        name='org_create_member'),
    url(r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/basic_info',
        OrgCreateMemberBasicInfoView.as_view(),
        name='org_create_member_basic_info'),
    url(r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/verify_identity',
        OrgCreateMemberVerifyIdentityView.as_view(),
        name='org_create_member_verify_identity'),
    url(r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/additional_info',
        OrgCreateMemberAdditionalInfoInfoView.as_view(),
        name='org_create_member_additional_info'),
    url(r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/almost_done',
        OrgCreateMemberAlmostDoneView.as_view(),
        name='org_create_member_almost_done'),
    url(r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/complete',
        OrgCreateMemberCompleteView.as_view(),
        name='org_create_member_complete'),
    url(r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/success',
        OrgCreateMemberSuccessView.as_view(),
        name='org_create_member_success'),
]
