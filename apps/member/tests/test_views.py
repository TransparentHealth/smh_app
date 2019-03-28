from httmock import all_requests, HTTMock

from django.test import TestCase
from django.urls.exceptions import NoReverseMatch
from django.urls import reverse

from apps.common.tests.base import SMHAppTestMixin
from apps.common.tests.factories import UserFactory
from apps.org.models import (
    ResourceGrant, REQUEST_APPROVED, REQUEST_DENIED, REQUEST_REQUESTED
)
from apps.org.tests.factories import (
    OrganizationFactory, ResourceGrantFactory, ResourceRequestFactory,
    UserSocialAuthFactory
)
from apps.sharemyhealth.resources import Resource


class MemberDashboardTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:dashboard'

    def test_member_dashboard(self):
        """GETting member dashboard shows ResourceRequests for request.user's resources."""
        # Some ResourceRequests for the request.user that have not yet been granted
        expected_resource_request_ids = [
            ResourceRequestFactory(
                member=self.user,
                status=REQUEST_REQUESTED
            ).id for i in range(0, 3)
        ]
        # Some ResourceRequests for other users
        for i in range(0, 2):
            ResourceRequestFactory()
        # Some ResourceRequests for the request.user that have been granted
        expected_resources_granted_ids = []
        for i in range(0, 3):
            resource_request = ResourceRequestFactory(
                member=self.user,
                status=REQUEST_APPROVED
            )
            ResourceGrantFactory(
                member=self.user,
                resource_request=resource_request
            )
            expected_resources_granted_ids.append(resource_request.id)
        # Some ResourceGrants for other users
        for i in range(0, 2):
            ResourceGrantFactory()
        # Some ResourceRequests for the request.user that have been denied/revoked
        for i in range(0, 3):
            ResourceRequestFactory(member=self.user, status=REQUEST_DENIED)

        response = self.client.get(reverse(self.url_name))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context_data['resource_requests'].values_list('id', flat=True)),
            set(expected_resource_request_ids)
        )
        self.assertEqual(
            set(response.context_data['resources_granted'].values_list('id', flat=True)),
            set(expected_resources_granted_ids)
        )

    def test_authenticated(self):
        """The user must be authenticated to see the member dashboard."""
        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            response = self.client.get(reverse(self.url_name))
            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.get(reverse(self.url_name))
            expected_redirect = '{}?next={}'.format(
                reverse('login'),
                reverse(self.url_name)
            )
            self.assertRedirects(response, expected_redirect)


class ApproveResourceRequestTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:approve_resource_request'

    def setUp(self):
        super().setUp()
        # A ResourceRequest for the self.user
        self.resource_request = ResourceRequestFactory(
            member=self.user,
            resourcegrant=None,
            status=REQUEST_REQUESTED
        )

    def test_methods(self):
        """Only the POST method is allowed."""
        url = reverse(self.url_name, kwargs={'pk': self.resource_request.pk})

        with self.subTest('GET'):
            response_get = self.client.get(url)
            self.assertEqual(response_get.status_code, 405)

        with self.subTest('PUT'):
            response_put = self.client.put(url, data={})
            self.assertEqual(response_put.status_code, 405)

        with self.subTest('PATCH'):
            response_patch = self.client.patch(url, data={})
            self.assertEqual(response_patch.status_code, 405)

        with self.subTest('DELETE'):
            response_delete = self.client.delete(url)
            self.assertEqual(response_delete.status_code, 405)

    def test_authenticated(self):
        """The user must be authenticated to approve ResourceRequests."""
        url = reverse(self.url_name, kwargs={'pk': self.resource_request.pk})

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.post(url)
            expected_redirect = '{}?next={}'.format(reverse('home'), url)
            self.assertRedirects(response, expected_redirect)

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            response = self.client.post(url)
            self.assertRedirects(response, reverse('member:dashboard'))

    def test_non_user_resource_request(self):
        """Approving a ResourceRequest that isn't for the request.user is not allowed."""
        resource_request_other_user = ResourceRequestFactory()

        url = reverse(self.url_name, kwargs={'pk': resource_request_other_user.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

    def test_approve_success(self):
        """A member may approve a ResourceRequest for them, which updates objects in the db."""
        url = reverse(self.url_name, kwargs={'pk': self.resource_request.pk})
        response = self.client.post(url)

        # The user is redirected to the member dashboard
        self.assertRedirects(response, reverse('member:dashboard'))
        # The self.resource_request's status is now 'Approved'
        self.resource_request.refresh_from_db()
        self.assertEqual(self.resource_request.status, REQUEST_APPROVED)
        # The self.resource_request now has a ResourceGrant
        self.assertIsNotNone(self.resource_request.resourcegrant)


class RevokeResourceRequestTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:revoke_resource_request'

    def setUp(self):
        super().setUp()
        # A ResourceRequest for the self.user that has been approved
        self.resource_request = ResourceRequestFactory(
            member=self.user,
            resourcegrant=None,
            status=REQUEST_APPROVED
        )
        ResourceGrantFactory(
            member=self.user,
            resource_request=self.resource_request,
            organization=self.resource_request.organization,
            resource_class_path=self.resource_request.resource_class_path
        )

    def test_methods(self):
        """Only the POST method is allowed."""
        url = reverse(self.url_name, kwargs={'pk': self.resource_request.pk})

        with self.subTest('GET'):
            response_get = self.client.get(url)
            self.assertEqual(response_get.status_code, 405)

        with self.subTest('PUT'):
            response_put = self.client.put(url, data={})
            self.assertEqual(response_put.status_code, 405)

        with self.subTest('PATCH'):
            response_patch = self.client.patch(url, data={})
            self.assertEqual(response_patch.status_code, 405)

        with self.subTest('DELETE'):
            response_delete = self.client.delete(url)
            self.assertEqual(response_delete.status_code, 405)

    def test_authenticated(self):
        """The user must be authenticated to approve ResourceRequests."""
        url = reverse(self.url_name, kwargs={'pk': self.resource_request.pk})

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.post(url)
            expected_redirect = '{}?next={}'.format(reverse('home'), url)
            self.assertRedirects(response, expected_redirect)

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            response = self.client.post(url)
            self.assertRedirects(response, reverse('member:dashboard'))

    def test_non_user_resource_request(self):
        """Revoking a ResourceRequest that isn't for the request.user is not allowed."""
        resource_request_other_user = ResourceRequestFactory(status=REQUEST_APPROVED)
        ResourceGrantFactory(
            member=resource_request_other_user.member,
            organization=resource_request_other_user.organization,
            resource_class_path=resource_request_other_user.resource_class_path
        )

        url = reverse(self.url_name, kwargs={'pk': resource_request_other_user.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

    def test_revoke_success(self):
        """A member may revoke a ResourceRequest for them, which updates objects in the db."""
        # The id of the ResourceGrant for the self.resource_request
        resource_grant_id = self.resource_request.resourcegrant.id

        url = reverse(self.url_name, kwargs={'pk': self.resource_request.pk})
        response = self.client.post(url)

        # The user is redirected to the member dashboard
        self.assertRedirects(response, reverse('member:dashboard'))
        # The self.resource_request's status is now 'Denied'
        self.resource_request.refresh_from_db()
        self.assertEqual(self.resource_request.status, REQUEST_DENIED)
        # The self.resource_request no longer has a ResourceGrant, since it has been deleted
        self.assertIsNone(getattr(self.resource_request, 'resourcegrant', None))
        self.assertFalse(ResourceGrant.objects.filter(id=resource_grant_id).exists())

    def test_deny(self):
        """A member make POST to deny a ResourceRequest, which updates objects in the db."""
        # A ResourceRequest for the self.user, which does not have a ResourceGrant,
        # which means that it has been requested, but not approved.
        self.resource_request.status = REQUEST_REQUESTED
        self.resource_request.resourcegrant.delete()
        self.resource_request.save()

        url = reverse(self.url_name, kwargs={'pk': self.resource_request.pk})
        response = self.client.post(url)

        # The user is redirected to the member dashboard
        self.assertRedirects(response, reverse('member:dashboard'))
        # The self.resource_request's status is now 'Denied'
        self.resource_request.refresh_from_db()
        self.assertEqual(self.resource_request.status, REQUEST_DENIED)
        # The self.resource_request does not have a ResourceGrant
        self.assertIsNone(getattr(self.resource_request, 'resourcegrant', None))


class RecordsViewTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:records'

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

    def test_context_data(self):
        """GETting records view puts response of get_member_data() into the context."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        url = reverse(self.url_name, kwargs={'pk': member.pk})
        # We mock the use of the requests library, so we don't make real
        # requests from within the test.
        with HTTMock(self.response_content_success):
            response = self.client.get(url)

        # The response has data,
        # which matches the mocked response.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data.get('data').json(),
            self.expected_response_success['content']
        )

    def test_authenticated(self):
        """The user must be authenticated to see records."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)
        url = reverse(self.url_name, kwargs={'pk': member.pk})

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.get(url)
            expected_redirect = '{}?next={}'.format(
                reverse('login'),
                url
            )
            self.assertRedirects(response, expected_redirect)


class DataSourcesViewTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:data-sources'

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

    def test_get_parameters(self):
        """GETting data sources view with/without resource_name and record_type parameters."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        with self.subTest('no resource_name or record_type parameters'):
            url = reverse(self.url_name, kwargs={'pk': member.pk})

            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            # Because the user did not specify a resource_name, the response has
            # no data.
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context_data.get('data'), None)

        with self.subTest('no record_type parameter', resource_name=provider_name):
            url = reverse(
                self.url_name,
                kwargs={'pk': member.pk, 'resource_name': provider_name}
            )

            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            # Since the user specified a resource_name, the response has data,
            # which matches the mocked response.
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context_data.get('data').json(),
                self.expected_response_success['content']
            )

        with self.subTest('no resource_name parameter', record_type='all'):
            # A URL for data-soruces with a record_type parameter but no
            # resource_name parameter does not exist.
            with self.assertRaises(NoReverseMatch):
                url = reverse(
                    self.url_name,
                    kwargs={'pk': member.pk, 'record_type': 'all'}
                )

        with self.subTest(resource_name='sharemyhealth', record_type='all'):
            url = reverse(
                self.url_name,
                kwargs={
                    'pk': member.pk,
                    'resource_name': provider_name,
                    'record_type': 'all'
                }
            )

            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            # Since the user specified a resource_name and a record_type, the
            # response has data, which matches the mocked response.
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context_data.get('data').json(),
                self.expected_response_success['content']
            )

    def test_authenticated(self):
        """The user must be authenticated to see data sources."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)
        url = reverse(
            self.url_name,
            kwargs={
                'pk': member.pk,
                'resource_name': provider_name,
                'record_type': 'all'
            }
        )

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.get(url)
            expected_redirect = '{}?next={}'.format(reverse('login'), url)
            self.assertRedirects(response, expected_redirect)
