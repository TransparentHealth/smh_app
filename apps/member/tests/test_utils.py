import json
from httmock import HTTMock

from django.conf import settings
from django.shortcuts import Http404
from django.test import TestCase

from apps.common.tests.base import MockResourceDataMixin, SMHAppTestMixin
from apps.common.tests.factories import UserFactory
from apps.org.models import ResourceGrant
from apps.sharemyhealth.resources import Resource
from ..utils import get_member_data


class GetMemberDataTestCase(MockResourceDataMixin, SMHAppTestMixin, TestCase):

    def test_get_member_data_success(self):
        """A successful request to get data for a member."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_user_access_to_member_token(self.user, member, provider_name)

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
        self.give_user_access_to_member_token(self.user, member, provider_name)

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
        self.give_user_access_to_member_token(self.user, member, provider_name)

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

    def test_own_data(self):
        """Requesting to GET the member's own data is ok, even without a ResourceGrant."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token. This creates a
        # ResourceGrant for the member's access_token to the request.user's Organization.
        provider_name = Resource.name
        self.give_user_access_to_member_token(self.user, member, provider_name)

        with self.subTest('with ResourceGrant'):
            # We mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                # The member (not the self.user) requests access to the member's data.
                response = get_member_data(member, member.member, provider_name, 'all')

            self.assertEqual(response.status_code, 200)

        with self.subTest('without ResourceGrant'):
            # Remove the ResourceGrant for the member's access_token.
            ResourceGrant.objects.filter(member=member).delete()

            # We mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                # The member (not the self.user) requests access to the member's data.
                response = get_member_data(member, member.member, provider_name, 'all')

            self.assertEqual(response.status_code, 200)
