import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from httmock import all_requests, HTTMock
from social_django.models import UserSocialAuth

from apps.common.tests.base import SMHAppTestMixin
from apps.member.models import Member
from apps.org.tests.factories import UserSocialAuthFactory
from .factories import OrganizationFactory
from ..models import Organization


class OrganizationDashboardTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:dashboard'

    def test_user_organizations(self):
        """GETting the organization dashboard shows the user's organizations."""
        # An Organization associated with the self.user
        organization = OrganizationFactory()
        organization.users.add(self.user)
        # An Organization not associated with the self.user
        OrganizationFactory()

        response = self.client.get(reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context_data['organizations'].values_list('id', flat=True)),
            set([organization.id])
        )

    def test_authenticated(self):
        """The user must be authenticated to see the dashboard."""
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


class CreateOrganizationTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:organization-add'

    def test_create_organizations(self):
        """The user may create an Organization."""
        data = {'name': 'New Organization'}
        # Currently, there are no Organizations
        self.assertEqual(Organization.objects.count(), 0)

        response = self.client.post(reverse(self.url_name), data=data)

        self.assertRedirects(response, reverse('org:dashboard'))
        # An Organization has been created
        self.assertEqual(Organization.objects.count(), 1)
        new_organization = Organization.objects.first()
        self.assertEqual(new_organization.name, data['name'])
        # The Organization's creator is automatically associated with the new
        # Organization, even though the user didn't add themselves in the form data.
        self.assertEqual(
            set(new_organization.users.values_list('id', flat=True)),
            set([self.user.id])
        )

    def test_authenticated(self):
        """The user must be authenticated to create an Organization."""
        with self.subTest('Authenticated'):
            self.client.force_login(self.user)
            response = self.client.post(reverse(self.url_name), data={'name': 'New Org 2'})
            self.assertRedirects(response, reverse('org:dashboard'))

        with self.subTest('Not authenticated'):
            self.client.logout()
            response = self.client.post(reverse(self.url_name), data={'name': 'New Org 3'})
            expected_redirect = '{}?next={}'.format(
                reverse('login'),
                reverse(self.url_name)
            )
            self.assertRedirects(response, expected_redirect)


class UpdateOrganizationTestCase(SMHAppTestMixin, TestCase):
    def test_update_organizations(self):
        """The user may update an Organization."""
        # An Organization associated with the self.user
        organization = OrganizationFactory()
        organization.users.add(self.user)

        data = {'name': 'New Name'}
        url = reverse('org:organization-update', kwargs={'pk': organization.pk})

        response = self.client.post(url, data=data)

        self.assertRedirects(response, reverse('org:dashboard'))
        # The Organization has been updated
        organization.refresh_from_db()
        self.assertEqual(organization.name, data['name'])

    def test_update_organization_not_associated(self):
        """A user may not update an Organization that the user is not associated with."""
        # An Organization not associated with the self.user
        org_not_associated = OrganizationFactory()

        data = {'name': 'New Name'}
        url = reverse('org:organization-update', kwargs={'pk': org_not_associated.pk})

        with self.subTest('GET'):
            response_get = self.client.get(url, data=data)
            self.assertEqual(response_get.status_code, 404)

        with self.subTest('POST'):
            response_post = self.client.post(url, data=data)

            self.assertEqual(response_post.status_code, 404)
            # The Organization has not been updated
            org_not_associated.refresh_from_db()
            self.assertNotEqual(org_not_associated.name, data['name'])

    def test_authenticated(self):
        """The user must be authenticated to update an Organization."""
        # An Organization associated with the self.user
        organization = OrganizationFactory()
        organization.users.add(self.user)

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)

            data = {'name': 'New Name 1'}
            url = reverse('org:organization-update', kwargs={'pk': organization.pk})
            response = self.client.post(url, data=data)

            self.assertRedirects(response, reverse('org:dashboard'))

        with self.subTest('Not authenticated'):
            self.client.logout()

            data = {'name': 'New Name 2'}
            url = reverse('org:organization-update', kwargs={'pk': organization.pk})
            response = self.client.post(url, data=data)

            expected_redirect = '{}?next={}'.format(reverse('login'), url)
            self.assertRedirects(response, expected_redirect)


class DeleteOrganizationTestCase(SMHAppTestMixin, TestCase):
    def test_delete_organization(self):
        """The user may delete an Organization."""
        # An Organization associated with the self.user
        organization = OrganizationFactory()
        organization.users.add(self.user)

        url = reverse('org:organization-delete', kwargs={'pk': organization.pk})

        response = self.client.post(url)

        self.assertRedirects(response, reverse('org:dashboard'))
        # The Organization has been deleted
        self.assertFalse(Organization.objects.filter(pk=organization.pk).exists())

    def test_delete_organization_not_associated(self):
        """A user may not delete an Organization that the user is not associated with."""
        # An Organization not associated with the self.user
        org_not_associated = OrganizationFactory()

        url = reverse('org:organization-delete', kwargs={'pk': org_not_associated.pk})

        with self.subTest('GET'):
            response_get = self.client.get(url)
            self.assertEqual(response_get.status_code, 404)

        with self.subTest('POST'):
            response_post = self.client.post(url)

            self.assertEqual(response_post.status_code, 404)
            # The Organization has not been deleted
            self.assertTrue(Organization.objects.filter(pk=org_not_associated.pk).exists())

    def test_authenticated(self):
        """The user must be authenticated to delete an Organization."""
        # An Organization associated with the self.user
        organization = OrganizationFactory()
        organization.users.add(self.user)

        with self.subTest('Authenticated'):
            self.client.force_login(self.user)

            url = reverse('org:organization-delete', kwargs={'pk': organization.pk})
            response = self.client.post(url)

            self.assertRedirects(response, reverse('org:dashboard'))

        with self.subTest('Not authenticated'):
            self.client.logout()

            url = reverse('org:organization-delete', kwargs={'pk': organization.pk})
            response = self.client.post(url)

            expected_redirect = '{}?next={}'.format(reverse('login'), url)
            self.assertRedirects(response, expected_redirect)


class OrgCreateMemberViewTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member'

    def setUp(self):
        super().setUp()
        # An Organization associated with the self.user
        self.organization = OrganizationFactory()
        self.organization.users.add(self.user)
        # The URL for creating a Member associated with the self.organization
        self.url = reverse(self.url_name, kwargs={'org_slug': self.organization.slug})

    @all_requests
    def response_content_success(self, url, request):
        """The response for a successful POST to VMI."""
        phone_number = request.original.data.get('phone_number')
        if phone_number == 'none':
            content = self.get_successful_response_data_from_vmi(
                request.original.data.get('given_name'),
                request.original.data.get('family_name'),
                request.original.data.get('preferred_username')
            )
        else:
            content = self.get_successful_response_data_from_vmi(
                request.original.data.get('given_name'),
                request.original.data.get('family_name'),
                request.original.data.get('preferred_username'),
                request.original.data.get('phone_number'),
            )
        return {
            'status_code': 201,
            'content': content
        }

    def get_successful_response_data_from_vmi(
        self,
        first_name,
        last_name,
        username,
        phone_number=None
    ):
        """The expected content of a response for a successful POST to create a VMI user."""
        return {
            'email': 'test_{}_{}@example.com'.format(first_name, last_name),
            'exp': 1555518026.550254,
            'iat': 1555514426.5502696,
            'iss': settings.SOCIAL_AUTH_VMI_HOST,
            'sub': random.randint(100000000000000, 999999999999999),
            'aal': '1',
            'birthdate': '2000-01-01',
            'email_verified': False,
            'family_name': last_name,
            'given_name': first_name,
            'ial': '1',
            'name': '{} {}'.format(first_name, last_name),
            'nickname': first_name,
            'phone_number': phone_number if phone_number else 'nophone',
            'phone_verified': False,
            'picture': 'http://localhost:8000/media/profile-picture/None/no-img.jpg',
            'preferred_username': username,
            'vot': 'P0.Cc',
            'website': '',
            'address': [],
            'document': []
        }

    def test_get(self):
        """GETting the org_create_member view shows a form to create a new Member."""
        with self.subTest('An Organization that request.user is associated with'):
            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['organization'], self.organization)

        with self.subTest('An Organization that request.user is not associated with'):
            # An Organization not associated with the self.user
            organization2 = OrganizationFactory()
            # The URL for creating a Member associated with the organization2
            url_organization2 = reverse(self.url_name, kwargs={'org_slug': organization2.slug})

            response = self.client.get(url_organization2)

            self.assertEqual(response.status_code, 404)

    def test_post(self):
        """POSTing to the org_create_member view can create a new Member."""
        expected_num_members = Member.objects.count()
        expected_num_user_social_auths = UserSocialAuth.objects.count()

        with self.subTest('no data'):
            response = self.client.post(self.url, data={})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {
                    'first_name': ['This field is required.'],
                    'last_name': ['This field is required.'],
                    'username': ['This field is required.']
                }
            )
            # No Member was created, and no UserSocialAuth was created
            self.assertEqual(Member.objects.count(), expected_num_members)
            self.assertEqual(UserSocialAuth.objects.count(), expected_num_user_social_auths)

        with self.subTest('incomplete data'):
            data = {'first_name': 'New', 'last_name': 'Member'}
            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {'username': ['This field is required.']}
            )
            # No Member was created, and no UserSocialAuth was created
            self.assertEqual(Member.objects.count(), expected_num_members)
            self.assertEqual(UserSocialAuth.objects.count(), expected_num_user_social_auths)

        with self.subTest('valid data, no request.user UserSocialAuth object'):
            # If the request.user does not have a UserSocialAuth object for VMI,
            # then the response is an error.
            data = {'first_name': 'New', 'last_name': 'Member', 'username': 'new_member'}

            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['errors'],
                {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            )

            # No Member was created, and no UserSocialAuth was created
            self.assertEqual(Member.objects.count(), expected_num_members)
            self.assertEqual(UserSocialAuth.objects.count(), expected_num_user_social_auths)

        with self.subTest('valid data, and request.user has a UserSocialAuth object'):
            # Create a UserSocialAuth object for the self.user for VMI
            UserSocialAuthFactory(
                user=self.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'accessTOKENhere'}
            )
            expected_num_user_social_auths += 1

            # The data POSTed to the org_create_member view
            data = {'first_name': 'New', 'last_name': 'Member', 'username': 'new_member'}

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_content_success):
                response = self.client.post(self.url, data=data)

            # A successful create redirects to the next page of the creation process.
            expected_url_next_page = reverse(
                'org:org_create_member_basic_info',
                kwargs={
                    'org_slug': self.organization.slug,
                    'username': data['username']
                }
            )
            self.assertRedirects(response, expected_url_next_page)
            # A Member was created, and a UserSocialAuth was created
            expected_num_members += 1
            expected_num_user_social_auths += 1
            self.assertEqual(Member.objects.count(), expected_num_members)
            self.assertEqual(
                get_user_model().objects.filter(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    username=data['username'],
                ).count(),
                1
            )
            self.assertEqual(UserSocialAuth.objects.count(), expected_num_user_social_auths)
            # The new Member is associated with the relevant Organization
            new_member = Member.objects.get(user__username=data['username'])
            self.assertTrue(self.organization in new_member.organizations.all())

    def test_authenticated(self):
        """The user must be authenticated to use the org_create_member view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Authenticated POST'):
            self.client.force_login(self.user)
            response = self.client.post(self.url, data={})
            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated GET'):
            self.client.logout()

            response = self.client.get(self.url)

            expected_redirect = '{}?next={}'.format(reverse('home'), self.url)
            self.assertRedirects(response, expected_redirect)

        with self.subTest('Not authenticated POST'):
            self.client.logout()

            response = self.client.post(self.url, data={})

            expected_redirect = '{}?next={}'.format(reverse('home'), self.url)
            self.assertRedirects(response, expected_redirect)
