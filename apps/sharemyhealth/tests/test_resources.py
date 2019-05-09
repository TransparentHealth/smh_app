from httmock import all_requests, HTTMock

from django.test import TestCase

from apps.org.tests.factories import UserSocialAuthFactory
from apps.common.tests.factories import UserFactory
from ..resources import Resource


class ResourceTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.member = UserFactory()
        # When we mock uses of the requests library in this test class, this is
        # the expected mock response.
        self.expected_response_success = {
            'status_code': 200,
            'content': {'test_key': 'Test content'}
        }

    @all_requests
    def response_content_success(self, url, request):
        """Return the response for when we mock uses of the requests library."""
        return self.expected_response_success

    def test_init(self):
        """Initializing a Resource sets the member and db_object."""
        with self.subTest('Initializing Resource requires a member'):
            with self.assertRaises(TypeError):
                Resource()

        with self.subTest('Initializing Resource sets member and db_object'):
            # A UserSocialAuth object for the self.member and the Resource
            user_social_auth = UserSocialAuthFactory(
                user=self.member,
                uid=self.member.id,
                provider=Resource.name,
            )
            # A UserSocialAuth object for the self.member, but for a different Resource
            UserSocialAuthFactory(user=self.member, uid=self.member.id, provider='other_resource')
            # A UserSocialAuth object for the Resource, but for a different member
            other_member = UserFactory()
            UserSocialAuthFactory(user=other_member, uid=other_member.id, provider=Resource.name)

            # Initializing the Resource sets the user_social_auth (for the
            # self.member and the Resource) as the db_object.
            resource = Resource(self.member)
            self.assertEqual(resource.member, self.member)
            self.assertEqual(resource.db_object, user_social_auth)

    def test_filter_by_user(self):
        """The filter_by_user() method returns the first UserSocialAuth object for member."""
        # A UserSocialAuth object for the self.member and the Resource
        self_member_result = UserSocialAuthFactory(
            user=self.member,
            uid=self.member.id,
            provider=Resource.name,
        )
        # A UserSocialAuth object for the self.member, but for a different Resource
        UserSocialAuthFactory(user=self.member, uid=self.member.id, provider='other_resource')
        # A UserSocialAuth object for the Resource, but for a different member
        other_member = UserFactory()
        other_member_result = UserSocialAuthFactory(
            user=other_member,
            uid=other_member.id,
            provider=Resource.name
        )

        resource = Resource(self.member)
        # Calling the filter_by_user() method filters the UserSocialAuth
        # objects for the appropriate member, even if it's not the member
        # that the Resource was instantiated for.
        self.assertEqual(
            set(resource.filter_by_user(self.member).values_list('id', flat=True)),
            set([self_member_result.id])
        )
        self.assertEqual(
            set(resource.filter_by_user(other_member).values_list('id', flat=True)),
            set([other_member_result.id])
        )

    def test_get(self):
        """Calling the .get() method makes a request to get the member's data."""
        # The member has received an access_token to get their own data.
        access_token = 'accessTOKENhere'
        refresh_token = 'refreshTOKEN'
        UserSocialAuthFactory(
            user=self.member,
            uid=self.member.id,
            provider=Resource.name,
            extra_data={'refresh_token': refresh_token, 'access_token': access_token}
        )
        resource = Resource(self.member)
        requested_record_type = 'prescriptions'

        # GET the data for the member.
        # Note: we mock the use of the requests library, so we don't make requests
        # from within the test.
        with HTTMock(self.response_content_success):
            data = resource.get(requested_record_type)

        # The response matches the self.response_content_success
        self.assertEqual(data.status_code, self.expected_response_success['status_code'])
        self.assertEqual(data.json(), self.expected_response_success['content'])
        # The request was made to a URL built from the Resource's url_for_data,
        # and the requested_record_type.
        expected_url = Resource.url_for_data.format(record_type=requested_record_type)
        self.assertEqual(data.request.url, expected_url)
        # The request was made with a 'Bearer' Authorization header that includes
        # the access_token.
        self.assertEqual(
            data.request.headers['Authorization'],
            'Bearer {}'.format(access_token)
        )
