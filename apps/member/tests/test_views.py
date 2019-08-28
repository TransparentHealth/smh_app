from django.test import TestCase, override_settings
from django.urls import reverse
from httmock import HTTMock

from apps.common.tests.base import MockResourceDataMixin, SMHAppTestMixin
from apps.common.tests.factories import UserFactory
from apps.notifications.models import Notification
from apps.org.models import (
    REQUEST_APPROVED,
    REQUEST_DENIED,
    REQUEST_REQUESTED,
    RESOURCE_CHOICES,
    ResourceGrant,
    ResourceRequest,
)
from apps.org.tests.factories import (
    OrganizationFactory,
    ResourceGrantFactory,
    ResourceRequestFactory,
    UserSocialAuthFactory,
)
from apps.sharemyhealth.resources import Resource


@override_settings(LOGIN_URL='/accounts/login/')
class MemberDashboardTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:dashboard'

    def test_member_dashboard(self):
        """GETting member dashboard shows notifications for request.user's resources."""
        # Some ResourceRequests for the request.user that have not yet been granted
        # expected_resource_request_ids = [
        #     ResourceRequestFactory(
        #         member=self.user,
        #         status=REQUEST_REQUESTED
        #     ).id for i in range(0, 3)
        # ]
        # Some ResourceRequests for other users
        for i in range(0, 2):
            ResourceRequestFactory()
        # Some ResourceRequests for the request.user that have been granted
        # expected_resources_granted_ids = []
        for i in range(0, 3):
            resource_request = ResourceRequestFactory(
                member=self.user, status=REQUEST_APPROVED
            )
            ResourceGrantFactory(member=self.user, resource_request=resource_request)
            # expected_resources_granted_ids.append(resource_request.id)
        # Some ResourceGrants for other users
        for i in range(0, 2):
            ResourceGrantFactory()
        # Some ResourceRequests for the request.user that have been denied/revoked
        for i in range(0, 3):
            ResourceRequestFactory(member=self.user, status=REQUEST_DENIED)

        response = self.client.get(reverse(self.url_name))

        self.assertEqual(response.status_code, 200)
        # self.assertEqual(
        #     set(response.context_data['resource_requests'].values_list('id', flat=True)),
        #     set(expected_resource_request_ids)
        # )
        # self.assertEqual(
        #     set(response.context_data['resources_granted'].values_list('id', flat=True)),
        #     set(expected_resources_granted_ids)
        # )

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
                reverse('login'), reverse(self.url_name)
            )
            self.assertRedirects(response, expected_redirect)


@override_settings(LOGIN_URL='/accounts/login/')
class ApproveResourceRequestTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:approve_resource_request'

    def setUp(self):
        super().setUp()
        # A ResourceRequest for the self.user
        self.resource_request = ResourceRequestFactory(
            member=self.user, resourcegrant=None, status=REQUEST_REQUESTED
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


@override_settings(LOGIN_URL='/accounts/login/')
class RevokeResourceRequestTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:revoke_resource_request'

    def setUp(self):
        super().setUp()
        # A ResourceRequest for the self.user that has been approved
        self.resource_request = ResourceRequestFactory(
            member=self.user, resourcegrant=None, status=REQUEST_APPROVED
        )
        ResourceGrantFactory(
            member=self.user,
            resource_request=self.resource_request,
            organization=self.resource_request.organization,
            resource_class_path=self.resource_request.resource_class_path,
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
            resource_class_path=resource_request_other_user.resource_class_path,
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


@override_settings(LOGIN_URL='/accounts/login/')
class RecordsViewTestCase(MockResourceDataMixin, SMHAppTestMixin, TestCase):
    url_name = 'member:records'

    def setUp(self):
        """
        Set the self.expected_response_success.

        The self.expected_response_success is set to a sample response for getting
        1 Condition (diagnosis) record from the resource server.
        """
        super().setUp()
        self.expected_response_success = self.get_member_health_data_condition()

    def test_context_data(self):
        """
        OUTDATED
        GETting records view puts response of get_member_data() into the context.
        """
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_user_access_to_member_token(self.user, member, provider_name)

        url = reverse(self.url_name, kwargs={'pk': member.pk, 'resource_name': 'list'})
        # We mock the use of the requests library, so we don't make real
        # requests from within the test.
        with HTTMock(self.response_content_success):
            response = self.client.get(url)

        # The response has data matches the mocked response.
        self.assertEqual(response.status_code, 200)

        # The self.expected_response_success includes 1 'Diagnoses' record
        # save for possible future implementation
        # diagnoses_results = [
        #     data for data in response.context_data.get('results') if data['name'] == 'Diagnoses'
        # ]
        # self.assertEqual(diagnoses_results[0]['total'], 1)

    def test_authenticated(self):
        """The user must be authenticated to see records."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_user_access_to_member_token(self.user, member, provider_name)
        url = reverse(self.url_name, kwargs={'pk': member.pk, 'resource_name': 'list'})

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.get(url)
            expected_redirect = '{}?next={}'.format(reverse('login'), url)
            self.assertRedirects(response, expected_redirect)


@override_settings(LOGIN_URL='/accounts/login/')
class DataSourcesViewTestCase(MockResourceDataMixin, SMHAppTestMixin, TestCase):
    url_name = 'member:data-sources'

    def test_get(self):
        """GET the data sources view."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_user_access_to_member_token(self.user, member, provider_name)

        url = reverse(self.url_name, kwargs={'pk': member.pk})

        # We mock the use of the requests library, so we don't make real
        # requests from within the test.
        with HTTMock(self.response_content_success):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_authenticated(self):
        """The user must be authenticated to see data sources."""
        # Create a member
        member = UserFactory()
        # Give the self.user access to the member's access_token.
        provider_name = Resource.name
        self.give_user_access_to_member_token(self.user, member, provider_name)
        url = reverse(self.url_name, kwargs={'pk': member.pk})

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.get(url)
            expected_redirect = '{}?next={}'.format(reverse('login'), url)
            self.assertRedirects(response, expected_redirect)

    def test_get_permissions(self):
        """
        A user may see a member's data sources, if:
          - the request.user is the member, or
          - the request.user is in an Organization that has an approved
            ResourceRequest for the member's data
        """
        # Create a member
        member = UserFactory()
        # The member has received an access_token to get their own data.
        provider_name = Resource.name
        access_token = 'accessTOKENhere'
        UserSocialAuthFactory(
            user=member,
            provider=provider_name,
            extra_data={'refresh_token': 'refreshTOKEN', 'access_token': access_token},
        )

        # The URLs that will be used in this test
        member_data_url = reverse(self.url_name, kwargs={'pk': member.pk})

        with self.subTest(
            "A member's data sources without an approved ResourceRequest"
        ):

            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(member_data_url)

            # The request.user does not have access to the member's data
            self.assertEqual(response.status_code, 302)

        with self.subTest(
            "A member's data sources with an approved ResourceRequest, other Organization"
        ):
            # The member has approved some Organization's request for the member's data
            organization = OrganizationFactory()
            resource_request = ResourceRequestFactory(
                member=member,
                organization=organization,
                resourcegrant=None,
                status=REQUEST_APPROVED,
            )
            resource_grant = ResourceGrantFactory(
                member=resource_request.member,
                organization=resource_request.organization,
                resource_class_path=resource_request.resource_class_path,
                resource_request=resource_request,
            )

            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(member_data_url)

            # The request.user now has access to the member's data
            self.assertEqual(response.status_code, 302)

        with self.subTest(
            "A member's data sources with approved ResourceRequest from request.user's Organization"
        ):
            # The request.user is now in the organization
            organization.agents.add(self.user)

            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(member_data_url)

            # The request.user does not have access to the member's data, since
            # the request.user is not in the organization.
            self.assertEqual(response.status_code, 200)

        with self.subTest('A member requesting their own data'):
            self.client.logout()
            self.client.force_login(member)

            # We mock the use of the requests library, so we don't make real
            # requests from within the test.
            with HTTMock(self.response_content_success):
                response = self.client.get(member_data_url)

            # The request.user has access to their own data, regardless of their
            # Organization.
            self.assertEqual(response.status_code, 200)

            # Even if we remove the ResourceRequest and ResourceGrant objects,
            # the member is allowed to see their own data.
            resource_request.delete()
            resource_grant.delete()
            with HTTMock(self.response_content_success):
                response = self.client.get(member_data_url)
            self.assertEqual(response.status_code, 200)


@override_settings(LOGIN_URL='/accounts/login/')
class OrganizationsViewTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:organizations'

    def setUp(self):
        """set up organizations that will be used in the tests."""
        super().setUp()
        # 3 orgs is sufficient
        self.organizations = [
            OrganizationFactory(name="Org %d" % i) for i in range(1, 4)
        ]

    def test_get(self):
        """The organizations GET view includes context['organizations'], with three values
        for the current (logged-in) request.user:
            {'current': [list of REQUEST_APPROVED ResourceRequests],
            'requested': [list of REQUEST_REQUESTED ResourceRequests],
            'available': [list of REQUEST_DENIED ResourceRequests + orgs w/no ResourceRequest]},
        which is based on the status of the ResourceRequests for the member.
        Only test GET member orgs data for the (logged-in) request.user.
        """
        member_orgs_url = reverse(self.url_name, kwargs={'pk': self.user.pk})
        resource_class_path = RESOURCE_CHOICES[0][0]

        with self.subTest('User should have no org ResourceRequests'):
            response = self.client.get(member_orgs_url)
            self.assertEqual(len(response.context_data['organizations']['current']), 0)
            self.assertEqual(
                len(response.context_data['organizations']['requested']), 0
            )
            self.assertEqual(
                len(response.context_data['organizations']['available']), 3
            )

        # create 1 approved and 1 requested resource request for the user
        resource_requests = [
            ResourceRequest.objects.create(
                organization=self.organizations[0],
                member=self.user,
                user=self.user,
                status=REQUEST_REQUESTED,
                resource_class_path=resource_class_path,
            ),
            ResourceRequest.objects.create(
                organization=self.organizations[1],
                member=self.user,
                user=self.user,
                status=REQUEST_APPROVED,
                resource_class_path=resource_class_path,
            ),
        ]

        with self.subTest('User should have 1 requested and 1 approved organization'):
            response = self.client.get(member_orgs_url)
            self.assertEqual(len(response.context_data['organizations']['current']), 1)
            self.assertEqual(
                len(response.context_data['organizations']['requested']), 1
            )
            self.assertEqual(
                len(response.context_data['organizations']['available']), 1
            )

        # now make the 'requested' request 'denied'
        resource_requests[0].status = REQUEST_DENIED
        resource_requests[0].save()

        with self.subTest('User should have 1 approved and 2 available organizations'):
            # one of the 'available' organizations has been denied
            response = self.client.get(member_orgs_url)
            self.assertEqual(len(response.context_data['organizations']['current']), 1)
            self.assertEqual(
                len(response.context_data['organizations']['requested']), 0
            )
            self.assertEqual(
                len(response.context_data['organizations']['available']), 2
            )


@override_settings(LOGIN_URL='/accounts/login/')
class ResourceRequestResponseTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:resource_request_response'

    def setUp(self):
        """set up organizations that will be used in the tests."""
        super().setUp()
        # 3 orgs is sufficient
        self.organizations = [
            OrganizationFactory(name="Org %d" % i) for i in range(1, 4)
        ]

    def test_post_valid(self):
        """Posting changes in a member's organizations should result in ResourceRequest changes."""
        # start with 1 requested organization
        resource_class_path = RESOURCE_CHOICES[0][0]
        request_url = reverse(self.url_name)

        with self.subTest(
            'POST approval for a requested resource '
            'should result in approved status and a new ResourceGrant'
        ):
            ResourceRequestFactory(
                organization=self.organizations[0],
                user=self.user,
                member=self.user,
                resource_class_path=resource_class_path,
                status=REQUEST_REQUESTED,
            )

            response = self.client.post(
                request_url,
                {
                    'approve': 'Approve It',  # value doesn't matter, just the key
                    'member': self.user.pk,
                    'organization': self.organizations[
                        0
                    ].pk,  # same as the requested org above
                },
            )
            resource_request = ResourceRequest.objects.filter(member=self.user).first()
            resource_grant = ResourceGrant.objects.filter(
                resource_request=resource_request
            ).first()

            self.assertEqual(
                response.status_code, 302
            )  # redirects, we don't care where
            self.assertEqual(resource_request.status, REQUEST_APPROVED)
            self.assertIsNotNone(resource_grant)

        with self.subTest(
            'POST approve for available resource '
            'should result in approved status and a new ResourceGrant'
        ):
            response = self.client.post(
                request_url,
                {
                    'approve': 'Approve It',  # value doesn't matter, just the key
                    'member': self.user.pk,
                    'organization': self.organizations[1].pk,  # no ResourceRequest
                },
            )
            resource_request = ResourceRequest.objects.filter(
                member=self.user, organization=self.organizations[1]
            ).first()
            resource_grant = ResourceGrant.objects.filter(
                resource_request=resource_request
            ).first()

            self.assertEqual(
                response.status_code, 302
            )  # redirects, we don't care where
            self.assertEqual(resource_request.status, REQUEST_APPROVED)
            self.assertIsNotNone(resource_grant)

        with self.subTest(
            'POST deny for requested resource '
            'should result in denied status and no ResourceGrants'
        ):
            ResourceRequestFactory(
                organization=self.organizations[2],
                user=self.user,
                member=self.user,
                resource_class_path=resource_class_path,
                status=REQUEST_REQUESTED,
            )
            organization = self.organizations[2]
            response = self.client.post(
                request_url,
                {
                    'deny': 'No way!',  # value doesn't matter, just the key
                    'member': self.user.pk,
                    'organization': organization.pk,  # requested
                },
            )
            resource_request = ResourceRequest.objects.filter(
                member=self.user, organization=organization
            ).first()
            resource_grant = ResourceGrant.objects.filter(
                resource_request=resource_request
            ).first()

            self.assertEqual(resource_request.status, REQUEST_DENIED)
            self.assertIsNone(resource_grant)

        with self.subTest(
            'POST revoke for approved resource '
            'should result in denied status and no ResourceGrants'
        ):
            # starting state: approved and granted (from above subTest)
            organization = self.organizations[1]
            resource_request = ResourceRequest.objects.filter(
                member=self.user, organization=organization
            ).first()
            resource_grant = ResourceGrant.objects.filter(
                resource_request=resource_request
            ).first()
            self.assertEqual(resource_request.status, REQUEST_APPROVED)
            self.assertIsNotNone(resource_grant)  # should exist from earlier subTest

            response = self.client.post(
                request_url,
                {
                    'deny': 'No way!',  # value doesn't matter, just the key
                    'member': self.user.pk,
                    'organization': organization.pk,  # requested
                },
            )
            resource_request = ResourceRequest.objects.filter(
                member=self.user, organization=organization
            ).first()
            resource_grant = ResourceGrant.objects.filter(
                resource_request=resource_request
            ).first()

            self.assertEqual(resource_request.status, REQUEST_DENIED)
            self.assertIsNone(resource_grant)  # should have been deleted

    def test_post_invalid(self):
        """Invalid post conditions should results HTTP 422 Unprocessable entity
        * 'member' does not exist
        * 'organization' does not exist
        * 'status' is not in ['approve', 'deny', 'revoke']
        """
        request_url = reverse(self.url_name)
        with self.subTest('post with non-existing member results in error message'):
            new_user = UserFactory()
            new_user_pk = new_user.pk
            new_user.delete()  # now we know they don't exist.
            response = self.client.post(
                request_url,
                {
                    'approve': 'Not gonna work',
                    'member': new_user_pk,
                    'organization': self.organizations[0].pk,
                },
            )
            self.assertEqual(response.status_code, 422)
            self.assertIn(b'member', response.content)  # error with the member field

        with self.subTest(
            'post with non-existing organization results in error message'
        ):
            new_org = OrganizationFactory()
            new_org_pk = new_org.pk
            new_org.delete()  # now we know they don't exist.
            response = self.client.post(
                request_url,
                {
                    'approve': 'Not gonna work',
                    'member': self.user.pk,
                    'organization': new_org_pk,
                },
            )
            self.assertEqual(response.status_code, 422)
            self.assertIn(
                b'organization', response.content
            )  # error with the organization field

        with self.subTest('post with wrong status results in error message'):
            response = self.client.post(
                request_url,
                {'member': self.user.pk, 'organization': self.organizations[0].pk},
            )
            self.assertEqual(response.status_code, 422)
            self.assertIn(b'status', response.content)  # error with the status field


@override_settings(LOGIN_URL='/accounts/login/')
class RedirectSubjectURLTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:subject_url'

    def test_exists(self):
        user_profile = self.user.userprofile
        user_profile.subject = '012345678901234'
        user_profile.save()

        subject_url = reverse(self.url_name, kwargs={'subject': user_profile.subject})
        member_url = reverse('member:member-profile', kwargs={'pk': self.user.pk})
        response = self.client.get(subject_url)

        self.assertRedirects(response, member_url, fetch_redirect_response=False)

    def test_not_exists(self):
        subject_url = reverse(self.url_name, kwargs={'subject': '012345678901234'})
        response = self.client.get(subject_url)
        self.assertEqual(response.status_code, 404)


@override_settings(LOGIN_URL='/accounts/login/')
class MemberNotificationsTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:notifications'

    def test_get(self):
        """The response context_data should include the notifications for request.user,
        but not the notifications created for another user.
        """
        for i in range(3):
            Notification.objects.create(
                notify=self.user, actor=self.user, message="Notify %d" % i
            )
        other_user = UserFactory()
        for i in range(1):
            Notification.objects.create(
                notify=other_user, actor=self.user, message="Notify %d" % i
            )

        response = self.client.get(reverse(self.url_name))

        self.assertEqual(response.status_code, 200)
        for notification in response.context_data['notifications']:
            self.assertEqual(notification.notify, self.user)
