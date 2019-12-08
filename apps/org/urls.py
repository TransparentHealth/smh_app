# Copyright Videntity Systems, Inc.
from django.conf.urls import url

from .views import (
    DashboardView,
    OrgCreateMemberAdditionalInfoInfoView,
    OrgCreateMemberAlmostDoneView,
    OrgCreateMemberBasicInfoView,
    OrgCreateMemberCompleteView,
    OrgCreateMemberInvalidTokenView,
    OrgCreateMemberSuccessView,
    OrgCreateMemberVerifyIdentityView,
    OrgCreateMemberView,
    SearchMembersAPI,
    SearchView,
)

# Copyright Videntity Systems Inc.

app_name = 'org'
urlpatterns = [
    url(r'^dashboard$', DashboardView.as_view(), name='dashboard'),

    # URLs for the process of having a User at an Organization create a new Member
    url(
        r'(?P<org_slug>[-\w]+)/create-member/create',
        OrgCreateMemberView.as_view(),
        name='org_create_member',
    ),
    url(
        r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/basic_info',
        OrgCreateMemberBasicInfoView.as_view(),
        name='org_create_member_basic_info',
    ),
    url(
        r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/verify_identity',
        OrgCreateMemberVerifyIdentityView.as_view(),
        name='org_create_member_verify_identity',
    ),
    url(
        r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/additional_info',
        OrgCreateMemberAdditionalInfoInfoView.as_view(),
        name='org_create_member_additional_info',
    ),
    url(
        r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/almost_done',
        OrgCreateMemberAlmostDoneView.as_view(),
        name='org_create_member_almost_done',
    ),
    url(
        r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/complete/(?P<uidb64>[-\wA-Z]+)/(?P<token>[-\w]+)/',
        OrgCreateMemberCompleteView.as_view(),
        name='org_create_member_complete',
    ),
    url(
        r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/invalid_token',
        OrgCreateMemberInvalidTokenView.as_view(),
        name='org_create_member_invalid_token',
    ),
    url(
        r'(?P<org_slug>[-\w]+)/create-member/(?P<username>[-\w]+)/success',
        OrgCreateMemberSuccessView.as_view(),
        name='org_create_member_success',
    ),
    url(r'^org-member-api$', SearchMembersAPI.as_view(), name='org_member_api'),
    url(r'^search$', SearchView.as_view(), name='search'),
]
