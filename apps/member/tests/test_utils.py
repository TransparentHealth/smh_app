import json
from httmock import all_requests, HTTMock

from django.conf import settings
from django.shortcuts import Http404
from django.test import TestCase

from apps.common.tests.base import SMHAppTestMixin
from apps.common.tests.factories import UserFactory
from apps.org.tests.factories import (
    OrganizationFactory, ResourceGrantFactory, ResourceRequestFactory,
    UserSocialAuthFactory
)
from apps.org.models import ResourceGrant, REQUEST_APPROVED
from apps.sharemyhealth.resources import Resource
from ..utils import get_member_data


class GetMemberDataTestCase(SMHAppTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        # When we mock uses of the requests library in this test class, this is
        # the expected mock response.
        self.expected_response_success = {
            'status_code': 200,
            'content': {'test_key': 'Test content'}
        }

    @all_requests
    def response_content_success(self, url, request):
        return self.expected_response_success

    def give_self_user_access_to_member_token(self, member, provider_name):
        """
        Give the self.user access to the member's access_token, and return access_token.

        This method creates the necessary database objects so that the self.user
        is in an Organization that has a ResourceGrant for the member's Resource,
        so the self.user can use the member's access_token to get data about the
        member.
        """
        # The self.user is a part of an Organization
        organization = OrganizationFactory()
        organization.users.add(self.user)
        # The member has received an access_token to get their own data.
        provider_name = provider_name
        access_token = 'accessTOKENhere'
        UserSocialAuthFactory(
            user=member,
            provider=provider_name,
            extra_data={'refresh_token': 'refreshTOKEN', 'access_token': access_token}
        )
        # The member has approved the Organization's request for the member's data
        resource_request = ResourceRequestFactory(
            member=member,
            organization=organization,
            resourcegrant=None,
            status=REQUEST_APPROVED
        )
        ResourceGrantFactory(
            member=resource_request.member,
            organization=resource_request.organization,
            resource_class_path=resource_request.resource_class_path,
            resource_request=resource_request
        )

    def test_get_member_data_success(self):
        """A successful request to get data for a member."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        # A user at the Organization (the self.user) gets the data for the member.
        # We mock the use of the requests library, so we don't make real requests
        # from within the test.
        with HTTMock(self.response_content_success):
            response = get_member_data(self.user, member.member, provider_name, 'all')

        # Here, we assert that the response has the expected mocked response.
        # More specific testing for the Resource.get() method exists in the
        # sharemyhealth app.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode()),
            self.expected_response_success['content']
        )

    def test_parameters(self):
        """Sending invalid parameters into get_member_data() returns a 404 response."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        with self.subTest('invalid resource_name parameter'):
            # We mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                # The resource_name parameter is not valid
                with self.assertRaises(Http404):
                    get_member_data(self.user, member.member, 'invalid_name', 'all')

        with self.subTest('invalid record_type parameter'):
            # Mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                # The resource_name record_type is not valid
                with self.assertRaises(Http404):
                    get_member_data(self.user, member.member, provider_name, 'invalid_name')

        for valid_resource_name in settings.RESOURCE_NAME_AND_CLASS_MAPPING.keys():
            for valid_record_type in settings.VALID_MEMBER_DATA_RECORD_TYPES:
                with self.subTest(
                    resource_name=valid_resource_name,
                    record_type=valid_record_type
                ):
                    # We mock the use of the requests library, so we don't make real requests
                    # from within the test.
                    with HTTMock(self.response_content_success):
                        response = get_member_data(self.user, member.member, provider_name, 'all')

                    self.assertEqual(response.status_code, 200)

    def test_resource_grant_needed(self):
        """Requesting to GET the member's data without a ResourceGrant returns a 404 response."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token. This creates a
        # ResourceGrant for the member's access_token to the request.user's Organization.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        with self.subTest('with ResourceGrant'):
            # We mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                response = get_member_data(self.user, member.member, provider_name, 'all')

            self.assertEqual(response.status_code, 200)

        with self.subTest('without ResourceGrant'):
            # Remove the ResourceGrant for the member's access_token to the
            # request.user's Organization.
            ResourceGrant.objects.filter(
                member=member,
                organization__users=self.user
            ).delete()

            # We mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                # Because the self.user's Organization no longer has a ResourceGrant
                # for the member's access_token, the an Http404 is raised.
                with self.assertRaises(Http404):
                    get_member_data(self.user, member.member, provider_name, 'all')