from httmock import all_requests, HTTMock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.common.tests.base import SMHAppTestMixin
from apps.common.tests.factories import UserFactory
from apps.org.tests.factories import (
    OrganizationFactory, ResourceGrantFactory, ResourceRequestFactory,
    UserSocialAuthFactory
)
from apps.org.models import (
    ResourceGrant, REQUEST_APPROVED, REQUEST_DENIED, REQUEST_REQUESTED
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


class GetMemberDataTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:get_member_data'

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

    def test_get(self):
        """A successful request to get data for a member."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        # A user at the Organization (the self.user) GETs the data for the member.
        url = reverse(
            self.url_name,
            kwargs={
                'pk': member.pk,
                'resource_name': provider_name,
                'record_type': 'prescriptions'
            }
        )
        # Mock the use of the requests library, so we don't make real requests
        # from within the test.
        with HTTMock(self.response_content_success):
            response = self.client.get(url)

        # Here, we assert that the response has the expected mocked response.
        # More specific testing for the Resource.get() method exists in the
        # sharemyhealth app.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['data'].json(),
            self.expected_response_success['content']
        )
        self.assertTemplateUsed(response, 'member/data.html')


    def test_authenticated(self):
        """The user must be authenticated to get a member's data."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        # The url that will be used during this test to try to get the member's data
        url = reverse(
            self.url_name,
            kwargs={
                'pk': member.pk,
                'resource_name': provider_name,
                'record_type': 'prescriptions'
            }
        )

        with self.subTest('Not authenticated'):
            self.client.logout()
            # Mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            expected_redirect = '{}?next={}'.format(reverse('home'), url)
            self.assertRedirects(response, expected_redirect)

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            # Mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

    def test_parameters(self):
        """Sending invalid parameters into the function returns a 404 response."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_self_user_access_to_member_token(member, provider_name)

        with self.subTest('invalid resource_name parameter'):
            url = reverse(
                self.url_name,
                kwargs={
                    'pk': member.pk,
                    'resource_name': 'invalid_name',
                    'record_type': 'prescriptions'
                }
            )

            # Mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            self.assertEqual(response.status_code, 404)

        with self.subTest('invalid record_type parameter'):
            url = reverse(
                self.url_name,
                kwargs={
                    'pk': member.pk,
                    'resource_name': provider_name,
                    'record_type': 'invalid_name'
                }
            )

            # Mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            self.assertEqual(response.status_code, 404)

        for valid_resource_name in settings.RESOURCE_NAME_AND_CLASS_MAPPING.keys():
            for valid_record_type in [
                'prescriptions', 'diagnoses', 'allergies', 'procedures', 'ed_reports',
                'family_history', 'demographics', 'discharge_summaries', 'immunizations',
                'lab_results', 'progress_notes', 'vital_signs'
            ]:
                with self.subTest(
                    resource_name=valid_resource_name,
                    record_type=valid_record_type
                ):
                    url = reverse(
                        self.url_name,
                        kwargs={
                            'pk': member.pk,
                            'resource_name': valid_resource_name,
                            'record_type': valid_record_type
                        }
                    )

                    # Mock the use of the requests library, so we don't make real
                    # requests from within the test.
                    with HTTMock(self.response_content_success):
                        response = self.client.get(url)

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
            url = reverse(
                self.url_name,
                kwargs={
                    'pk': member.pk,
                    'resource_name': provider_name,
                    'record_type': 'prescriptions'
                }
            )

            # Mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

        with self.subTest('without ResourceGrant'):
            # Remove the ResourceGrant for the member's access_token to the
            # request.user's Organization.
            ResourceGrant.objects.filter(
                member=member,
                organization__users=self.user
            ).delete()

            url = reverse(
                self.url_name,
                kwargs={
                    'pk': member.pk,
                    'resource_name': provider_name,
                    'record_type': 'prescriptions'
                }
            )
            # Mock the use of the requests library, so we don't make real requests
            # from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)

            # Because the self.user's Organization no longer has a ResourceGrant
            # for the member's access_token, the response has a 404 status_code.
            self.assertEqual(response.status_code, 404)
