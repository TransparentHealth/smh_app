import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse

from httmock import all_requests, remember_called, urlmatch, HTTMock
from social_django.models import UserSocialAuth

from apps.common.tests.base import SMHAppTestMixin
from apps.common.tests.factories import UserFactory
from apps.member.models import Member
from apps.org.tests.factories import UserSocialAuthFactory
from .factories import OrganizationFactory, ResourceRequestFactory
from ..models import (
    Organization, ResourceRequest, ResourceGrant, REQUEST_APPROVED, REQUEST_REQUESTED
)


@override_settings(LOGIN_URL='/accounts/login/')
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


@override_settings(LOGIN_URL='/accounts/login/')
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


@override_settings(LOGIN_URL='/accounts/login/')
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


@override_settings(LOGIN_URL='/accounts/login/')
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


@override_settings(LOGIN_URL='/accounts/login/')
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
        expected_num_resource_requests = ResourceRequest.objects.count()

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
            # No Member was created, and no UserSocialAuth or ResourceRequest was created
            self.assertEqual(Member.objects.count(), expected_num_members)
            self.assertEqual(UserSocialAuth.objects.count(), expected_num_user_social_auths)
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)

        with self.subTest('incomplete data'):
            data = {'first_name': 'New', 'last_name': 'Member'}
            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {'username': ['This field is required.']}
            )
            # No Member was created, and no UserSocialAuth or ResourceRequest was created
            self.assertEqual(Member.objects.count(), expected_num_members)
            self.assertEqual(UserSocialAuth.objects.count(), expected_num_user_social_auths)
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)

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

            # No Member was created, and no UserSocialAuth or ResourceRequest was created
            self.assertEqual(Member.objects.count(), expected_num_members)
            self.assertEqual(UserSocialAuth.objects.count(), expected_num_user_social_auths)
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)

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
            # The new Member's UserProfile has the picture_url from the VMI
            # response (from get_successful_response_data_from_vmi()).
            self.assertEqual(
                new_member.user.userprofile.picture_url,
                'http://localhost:8000/media/profile-picture/None/no-img.jpg'
            )
            # A new ResourceRequest was created from the Organization to the new Member
            expected_num_resource_requests += 1
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)
            self.assertEqual(
                ResourceRequest.objects.filter(
                    organization=self.organization,
                    member=new_member.user,
                    user=self.user
                ).count(),
                1
            )

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


@override_settings(LOGIN_URL='/accounts/login/')
class OrgCreateMemberBasicInfoViewTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member_basic_info'

    def setUp(self):
        super().setUp()
        # An Organization associated with the self.user
        self.organization = OrganizationFactory()
        self.organization.users.add(self.user)
        # A Member at the Organization
        self.member = UserFactory(email='test_{}@example.com'.format(random.random())).member
        self.organization.members.add(self.member)
        # The URL for creating a Member associated with the self.organization
        self.url = reverse(
            self.url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username
            }
        )

    @all_requests
    def response_content_success(self, url, request):
        """The response for a successful PUT to update a user in VMI."""
        # Get the UserSocialAuth based on the uid from the URL
        uid = request.original.url.split('/')[-2]
        user_social_auth = UserSocialAuth.objects.get(uid=uid)
        content = self.get_successful_response_data_from_vmi(
            user_social_auth.user.first_name,
            user_social_auth.user.last_name,
            user_social_auth.user.username,
            request.original.data.get('birthdate'),
            request.original.data.get('nickname'),
            request.original.data.get('gender'),
            request.original.data.get('email'),
        )
        return {
            'status_code': 200,
            'content': content
        }

    def get_successful_response_data_from_vmi(
        self,
        first_name,
        last_name,
        username,
        birthdate,
        nickname,
        gender,
        email
    ):
        """The expected content of a response for a successful PUT to update a VMI user."""
        return {
            'email': email,
            'exp': 1555518026.550254,
            'iat': 1555514426.5502696,
            'iss': settings.SOCIAL_AUTH_VMI_HOST,
            'sub': random.randint(100000000000000, 999999999999999),
            'aal': '1',
            'birthdate': birthdate,
            'email_verified': False,
            'family_name': last_name,
            'given_name': first_name,
            'ial': '1',
            'name': '{} {}'.format(first_name, last_name),
            'nickname': nickname,
            'phone_number': '+NoneNone',
            'phone_verified': False,
            'picture': 'http://localhost:8000/media/profile-picture/None/no-img.jpg',
            'preferred_username': username,
            'vot': 'P0.Cc',
            'website': '',
            'address': [],
            'document': []
        }

    def test_get(self):
        """GETting the org_create_member_basic_info view shows a form to update a Member."""
        subtests = (
            # user_at_org:         |  member_at_org:    | expected_success:
            # Is the request.user  | Is the Member      |  Should the
            # associated with the  | associated with    |  request
            # Organization?        | the Organization?  |  succeed?
            (True, True, True),
            (False, True, False),
            (True, False, False),
            (False, False, False),
        )
        for (user_at_org, member_at_org, expected_success) in subtests:
            organization = OrganizationFactory()
            if user_at_org:
                organization.users.add(self.user)
            member = UserFactory().member
            if member_at_org:
                organization.members.add(member)
            url = reverse(
                self.url_name,
                kwargs={'org_slug': organization.slug, 'username': member.user.username}
            )
            with self.subTest(
                user_at_org=user_at_org,
                member_at_org=member_at_org,
                expected_success=expected_success
            ):
                response = self.client.get(url)

                if expected_success:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['organization'], organization)
                    self.assertEqual(response.context['member'], member)
                else:
                    self.assertEqual(response.status_code, 404)

    def test_post(self):
        """POSTing to the org_create_member_basic_info view can update a Member."""
        with self.subTest('no data'):
            data = {}
            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {
                    'birthdate': ['This field is required.'],
                    # 'nickname': ['This field is required.'],
                    # 'email': ['This field is required.'],
                }
            )
            # The self.member was not updated
            self.member.user.refresh_from_db()
            self.assertNotEqual(self.member.user.email, data.get('email', ''))

        with self.subTest('incomplete data'):
            data = {'birthdate': '2000-01-01', 'gender': ''}
            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {
                    # 'nickname': ['This field is required.'],
                    # 'email': ['This field is required.']
                }
            )
            # The self.member was not updated
            self.member.user.refresh_from_db()
            self.assertNotEqual(self.member.user.email, data.get('email', ''))

        with self.subTest('invalid data'):
            data = {
                'birthdate': 'January 1, 2000',
                'nickname': 'Nickname',
                'gender': '',
                'email': 'new_email@example.com'
            }
            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {'birthdate': ['Enter a valid date.']}
            )
            # The self.member was not updated
            self.member.user.refresh_from_db()
            self.assertNotEqual(self.member.user.email, data.get('email', ''))

        with self.subTest('valid data, no request.user UserSocialAuth object'):
            # If the request.user does not have a UserSocialAuth object for VMI,
            # then the response is an error.
            data = {
                'birthdate': '2000-01-01',
                'nickname': 'Nickname',
                'gender': '',
                'email': 'new_email@example.com'
            }

            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['errors'],
                {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            )

            # The self.member was not updated
            self.member.user.refresh_from_db()
            self.assertNotEqual(self.member.user.email, data.get('email', ''))

        with self.subTest('valid data, no UserSocialAuth object for Member'):
            # If the Member does not have a UserSocialAuth object for VMI,
            # then the response is an error. In reality, this shouldn't happen,
            # since the UserSocialAuth object should get created for the new Member
            # during step 1 of the member creation process (the org_create_member_view),
            # but we handle the case that the UserSocialAuth object no longer exists.
            data = {
                'birthdate': '2000-01-01',
                'nickname': 'Nickname',
                'gender': '',
                'email': 'new_email@example.com'
            }
            # Create a UserSocialAuth object for the self.user for VMI
            UserSocialAuthFactory(
                user=self.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'accessTOKENhere'},
                uid=random.randint(100000000000000, 999999999999999),
            )

            response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['errors'],
                {'member': 'Member has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            )

            # The self.member was not updated
            self.member.user.refresh_from_db()
            self.assertNotEqual(self.member.user.email, data.get('email', ''))

        with self.subTest('valid data, request.user & member have a UserSocialAuth object'):
            # Create a UserSocialAuth object for the Member for VMI
            UserSocialAuthFactory(
                user=self.member.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'MeMbEraccessTOKEN'},
                uid=random.randint(100000000000000, 999999999999999),
            )

            # The data POSTed to the org_create_member_basic_info view
            data = {
                'birthdate': '2000-01-01',
                'nickname': 'Nickname',
                'gender': '',
                'email': 'new_email@example.com'
            }

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_content_success):
                response = self.client.post(self.url, data=data)

            # A successful create redirects to the next page of the creation process.
            expected_url_next_page = reverse(
                'org:org_create_member_verify_identity',
                kwargs={
                    'org_slug': self.organization.slug,
                    'username': self.member.user.username
                }
            )
            self.assertRedirects(response, expected_url_next_page)
            # The self.member was updated
            self.member.user.refresh_from_db()
            self.assertEqual(self.member.user.email, data.get('email', ''))
            # The self.member's UserProfile object's picture_url was updated based
            # on the value of 'picture' from get_successful_response_data_from_vmi()
            self.assertEqual(
                self.member.user.userprofile.picture_url,
                'http://localhost:8000/media/profile-picture/None/no-img.jpg'
            )

    def test_authenticated(self):
        """The user must be authenticated to use the org_create_member_basic_info view."""
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


@override_settings(LOGIN_URL='/accounts/login/')
class OrgCreateMemberVerifyIdentityTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member_verify_identity'
    next_url_name = 'org:org_create_member_almost_done'

    def setUp(self):
        super().setUp()
        # An Organization associated with the self.user
        self.organization = OrganizationFactory()
        self.organization.users.add(self.user)
        # A Member at the Organization
        self.member = UserFactory().member
        self.organization.members.add(self.member)
        # The URL for verifying the identity of a Member associated with the self.organization
        self.url = reverse(
            self.url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username
            }
        )
        self.next_url = reverse(
            self.next_url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username
            }
        )

    @urlmatch(path=r'^/api/v1/user/([0-9]+)?/id-assurance/$')
    @remember_called
    def response_id_assurance_list(self, url, request):
        """The response for a successful GET for a user's id assurances in VMI."""
        content = [self.sample_identity_assurance_response()]
        return {
            'status_code': 201,
            'content': content
        }

    @urlmatch(path=r'^/api/v1/user/([0-9]+)?/id-assurance/$')
    @remember_called
    def response_id_assurance_list_fail(self, url, request):
        """The response for an unsuccessful GET for a user's id assurances in VMI."""
        content = {'test_key': 'Error here'}
        return {
            'status_code': 400,
            'content': content
        }

    @urlmatch(path=r'^/api/v1/user/([0-9]+)?/id-assurance/([0-9a-zA-Z\-]+)?/$')
    @remember_called
    def response_id_assurance_detail(self, url, request):
        """The response for a successful GET for a user's id assurances in VMI."""
        return {
            'status_code': 200,
            'content': self.sample_identity_assurance_response()
        }

    def sample_identity_assurance_response(self):
        """The sample response from the VMI API for an identity assurance."""
        return {
            'id': 1,
            'classification': '',
            'description': 'This is the description',
            'exp': '2001-01-01',
            'verifier_subject': '997275294527729',
            'uuid': 'bc6b23c9-8a4e-40b8-a567-a31db5572ed8',
            'identity_proofing_mode': '',
            'action': '',
            'evidence': '',
            'id_verify_description': 'This is the description',
            'id_assurance_downgrade_description': '',
            'note': None,
            'metadata': {
                "subject_user": "member_username",
                "history": [
                    {
                        "verifying_user": "None",
                        "actions": "",
                        "updated_at": "None"
                    }
                ]
            },
            'type': '',
            'expires_at': '2001-01-01',
            'verification_date': None,
            'created_at': '2000-01-01T12:00:00.000000Z',
            'updated_at': '2000-01-01T12:00:00.000000Z',
            'subject_user': 2,  # The member's id in VMI
            'verifying_user': 1  # The request.user's id in VMI
        }

    def test_get(self):
        """GETting org_create_member_verify_identity view shows form to verify Member's identity."""
        subtests = (
            # user_at_org:         |  member_at_org:    | expected_success:
            # Is the request.user  | Is the Member      |  Should the
            # associated with the  | associated with    |  request
            # Organization?        | the Organization?  |  succeed?
            (True, True, True),
            (False, True, False),
            (True, False, False),
            (False, False, False),
        )
        for (user_at_org, member_at_org, expected_success) in subtests:
            organization = OrganizationFactory()
            if user_at_org:
                organization.users.add(self.user)
            member = UserFactory().member
            if member_at_org:
                organization.members.add(member)
            url = reverse(
                self.url_name,
                kwargs={'org_slug': organization.slug, 'username': member.user.username}
            )
            with self.subTest(
                user_at_org=user_at_org,
                member_at_org=member_at_org,
                expected_success=expected_success
            ):
                response = self.client.get(url)

                if expected_success:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['organization'], organization)
                    self.assertEqual(response.context['member'], member)
                else:
                    self.assertEqual(response.status_code, 404)

    def test_post(self):
        """POSTing to org_create_member_verify_identity view updates Member's identity assurance."""
        with self.subTest('no data'):
            data = {}
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_id_assurance_list, self.response_id_assurance_detail):
                response = self.client.post(self.url, data=data)

            self.assertRedirects(response, self.next_url)

            # No requests were made to VMI
            self.assertEqual(self.response_id_assurance_list.call['count'], 0)
            self.assertEqual(self.response_id_assurance_detail.call['count'], 0)

        with self.subTest('incomplete data'):
            data = {'description': 'description here', 'exp': '2020-01-01'}
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_id_assurance_list, self.response_id_assurance_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {
                    # 'classification': ['This field is required.']
                }
            )
            # No requests were made to VMI
            self.assertEqual(self.response_id_assurance_list.call['count'], 0)
            self.assertEqual(self.response_id_assurance_detail.call['count'], 0)

        with self.subTest('invalid data'):
            data = {
                'description': 'description',
                'exp': '2020-13-100',
                'classification': 'invalid classification',
            }
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_id_assurance_list, self.response_id_assurance_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            expected_errors = {
                'exp': ['Enter a valid date.'],
                'classification': [
                    'Select a valid choice. {} is not one of the available choices.'.format(
                        data['classification']
                    )
                ]
            }
            self.assertEqual(response.context['form'].errors, expected_errors)
            # No requests were made to VMI
            self.assertEqual(self.response_id_assurance_list.call['count'], 0)
            self.assertEqual(self.response_id_assurance_detail.call['count'], 0)

        with self.subTest('valid data, no request.user UserSocialAuth object'):
            # If the request.user does not have a UserSocialAuth object for VMI,
            # then the response is an error.
            data = {
                'description': 'description',
                'exp': '2099-01-01',
                'classification': 'ONE-SUPERIOR-OR-STRONG+',
            }
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_id_assurance_list, self.response_id_assurance_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['errors'],
                {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            )
            # No requests were made to VMI
            self.assertEqual(self.response_id_assurance_list.call['count'], 0)
            self.assertEqual(self.response_id_assurance_detail.call['count'], 0)

        with self.subTest('valid data, no UserSocialAuth object for Member'):
            # If the Member does not have a UserSocialAuth object for VMI,
            # then the response is an error. In reality, this shouldn't happen,
            # since the UserSocialAuth object should get created for the new Member
            # during step 1 of the member creation process (the org_create_member_view),
            # but we handle the case that the UserSocialAuth object no longer exists.
            data = {
                'description': 'description',
                'exp': '2099-01-01',
                'classification': 'ONE-SUPERIOR-OR-STRONG+',
            }
            # Create a UserSocialAuth object for the self.user for VMI
            UserSocialAuthFactory(
                user=self.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'accessTOKENhere'},
                uid=random.randint(100000000000000, 999999999999999),
            )

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_id_assurance_list, self.response_id_assurance_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['errors'],
                {'member': 'Member has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            )
            # No requests were made to VMI
            self.assertEqual(self.response_id_assurance_list.call['count'], 0)
            self.assertEqual(self.response_id_assurance_detail.call['count'], 0)

        with self.subTest('valid data, request.user & member have a UserSocialAuth object'):
            # Create a UserSocialAuth object for the Member for VMI
            UserSocialAuthFactory(
                user=self.member.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'MeMbEraccessTOKEN'},
                uid=random.randint(100000000000000, 999999999999999),
            )

            # The data POSTed to the org_create_member_basic_info view
            data = {
                'description': 'description',
                'exp': '2099-01-01',
                'classification': 'ONE-SUPERIOR-OR-STRONG+',
            }

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_id_assurance_list, self.response_id_assurance_detail):
                response = self.client.post(self.url, data=data)

            # A successful create redirects to the next page of the creation process.
            expected_url_next_page = reverse(
                # skip org:org_create_member_additional_info for now
                'org:org_create_member_almost_done',
                kwargs={
                    'org_slug': self.organization.slug,
                    'username': self.member.user.username
                }
            )
            self.assertRedirects(response, expected_url_next_page)
            # Several requests were made to VMI: 1 to get the member's identity
            # assurance uuid, and another to update the member's identity assurance.
            self.assertEqual(self.response_id_assurance_list.call['count'], 1)
            self.assertEqual(self.response_id_assurance_detail.call['count'], 0)

        with self.subTest('valid data, but request to VMI is not successful'):
            # The view makes a request to VMI to get the member's identity assurance
            # uuid. In case this request returns unsuccessfully, the error is
            # shown to the user.

            # The data POSTed to the org_create_member_basic_info view
            data = {
                'description': 'description',
                'exp': '2099-01-01',
                'classification': 'ONE-SUPERIOR-OR-STRONG+',
            }

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_id_assurance_list_fail, self.response_id_assurance_detail):
                response = self.client.post(self.url, data=data)

            # Since the GET to VMI returned as a non-successful response, the
            # error is shown to the user.
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['errors'], {'test_key': 'Error here'})
            # Only 1 request was made to VMI: to get the member's identity assurance
            # uuid. Since this request was not successful, no more requests to
            # VMI were made.
            self.assertEqual(self.response_id_assurance_list_fail.call['count'], 1)
            self.assertEqual(self.response_id_assurance_detail.call['count'], 0)

    def test_authenticated(self):
        """The user must be authenticated to use the org_create_member_verify_identity view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Authenticated POST'):
            self.client.force_login(self.user)
            response = self.client.post(self.url, data={})
            self.assertRedirects(response, self.next_url)

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


@override_settings(LOGIN_URL='/accounts/login/')
class OrgCreateMemberAdditionalInfoTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member_additional_info'

    def setUp(self):
        super().setUp()
        # An Organization associated with the self.user
        self.organization = OrganizationFactory()
        self.organization.users.add(self.user)
        # A Member at the Organization
        self.member = UserFactory().member
        self.organization.members.add(self.member)
        # The URL for verifying the identity of a Member associated with the self.organization
        self.url = reverse(
            self.url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username
            }
        )

    def test_get(self):
        """GETting org_create_member_additional_info view shows form to update Member's info."""
        subtests = (
            # user_at_org:         |  member_at_org:    | expected_success:
            # Is the request.user  | Is the Member      |  Should the
            # associated with the  | associated with    |  request
            # Organization?        | the Organization?  |  succeed?
            (True, True, True),
            (False, True, False),
            (True, False, False),
            (False, False, False),
        )
        for (user_at_org, member_at_org, expected_success) in subtests:
            organization = OrganizationFactory()
            if user_at_org:
                organization.users.add(self.user)
            member = UserFactory().member
            if member_at_org:
                organization.members.add(member)
            url = reverse(
                self.url_name,
                kwargs={'org_slug': organization.slug, 'username': member.user.username}
            )
            with self.subTest(
                user_at_org=user_at_org,
                member_at_org=member_at_org,
                expected_success=expected_success
            ):
                response = self.client.get(url)

                if expected_success:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['organization'], organization)
                    self.assertEqual(response.context['member'], member)
                else:
                    self.assertEqual(response.status_code, 404)

    def test_post(self):
        """POSTing to org_create_member_additional_info redirects the user to the next step."""
        with self.subTest('no data'):
            data = {}
            response = self.client.post(self.url, data=data)

            expected_url_next_page = reverse(
                'org:org_create_member_almost_done',
                kwargs={
                    'org_slug': self.organization.slug,
                    'username': self.member.user.username
                }
            )
            self.assertRedirects(response, expected_url_next_page)

    def test_authenticated(self):
        """The user must be authenticated to use the org_create_member_additional_info view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Authenticated POST'):
            self.client.force_login(self.user)
            response = self.client.post(self.url, data={})
            self.assertEqual(response.status_code, 302)

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


@override_settings(LOGIN_URL='/accounts/login/')
class OrgCreateMemberAlmostDoneTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member_almost_done'

    def setUp(self):
        super().setUp()
        # An Organization associated with the self.user
        self.organization = OrganizationFactory()
        self.organization.users.add(self.user)
        # A Member at the Organization
        self.member = UserFactory().member
        self.organization.members.add(self.member)
        # The URL for seeing that new Member creation at the self.organization is almost done
        self.url = reverse(
            self.url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username
            }
        )

    def test_get(self):
        """GETting org_create_member_almost_done view shows a page."""
        subtests = (
            # user_at_org:         |  member_at_org:    | expected_success:
            # Is the request.user  | Is the Member      |  Should the
            # associated with the  | associated with    |  request
            # Organization?        | the Organization?  |  succeed?
            (True, True, True),
            (False, True, False),
            (True, False, False),
            (False, False, False),
        )
        for (user_at_org, member_at_org, expected_success) in subtests:
            organization = OrganizationFactory()
            if user_at_org:
                organization.users.add(self.user)
            member = UserFactory().member
            if member_at_org:
                organization.members.add(member)
            url = reverse(
                self.url_name,
                kwargs={'org_slug': organization.slug, 'username': member.user.username}
            )
            with self.subTest(
                user_at_org=user_at_org,
                member_at_org=member_at_org,
                expected_success=expected_success
            ):
                response = self.client.get(url)

                if expected_success:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['organization'], organization)
                    self.assertEqual(response.context['member'], member)
                    # Verify the url_to_set_password in the context
                    member_uid = urlsafe_base64_encode(force_bytes(member.pk)).decode('utf-8')
                    member_token = token_generator.make_token(member.user)
                    expected_relative_url = reverse(
                        'org:org_create_member_complete',
                        kwargs={
                            'org_slug': organization.slug,
                            'username': member.user.username,
                            'uidb64': member_uid,
                            'token': member_token
                        }
                    )
                    expected_url = response.wsgi_request.build_absolute_uri(expected_relative_url)
                    self.assertEqual(response.context['url_to_set_password'], expected_url)
                else:
                    self.assertEqual(response.status_code, 404)

    def test_authenticated(self):
        """The user must be authenticated to use the org_create_member_almost_done view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Authenticated POST'):
            self.client.force_login(self.user)
            response = self.client.post(self.url, data={})
            self.assertEqual(response.status_code, 405)

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


@override_settings(LOGIN_URL='/accounts/login/')
class OrgCreateMemberCompleteTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member_complete'

    def setUp(self):
        super().setUp()
        self.organization = OrganizationFactory()
        # The self.user in this test is a member who is trying to set their password
        self.member = self.user.member
        self.organization.members.add(self.member)
        # It's assumed that the self.user is not authenticated, because they are
        # setting their password for the first time.
        self.client.logout()
        # The URL for completing new Member creation at the self.organization
        self.member_uid = urlsafe_base64_encode(force_bytes(self.member.pk)).decode('utf-8')
        self.member_token = token_generator.make_token(self.member.user)
        self.url = reverse(
            self.url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username,
                'uidb64': self.member_uid,
                'token': self.member_token
            }
        )

    @urlmatch(path=r'^/api/v1/user/([0-9]+)/$')
    @remember_called
    def response_user_detail(self, url, request):
        """The response for a successful PUT to update a user in VMI."""
        return {
            'status_code': 200,
            'content': self.get_sample_vmi_user_detail_response()
        }

    def get_sample_vmi_user_detail_response(self):
        """The expected content of a response for a VMI user detail."""
        return {
            'email': 'test_firstname_lastname@example.com',
            'exp': 1555518026.550254,
            'iat': 1555514426.5502696,
            'iss': settings.SOCIAL_AUTH_VMI_HOST,
            'sub': random.randint(100000000000000, 999999999999999),
            'aal': '1',
            'birthdate': '2000-01-01',
            'email_verified': False,
            'family_name': 'Lastname',
            'given_name': 'Firstname',
            'ial': '1',
            'name': 'Firstname Lastname',
            'nickname': 'Firstname',
            'phone_number': 'nophone',
            'phone_verified': False,
            'picture': 'http://localhost:8000/media/profile-picture/None/no-img.jpg',
            'preferred_username': 'username',
            'vot': 'P0.Cc',
            'website': '',
            'address': [],
            'document': []
        }

    def test_get(self):
        """GETting org_create_member_complete view shows a page."""
        subtests = (
            # user_at_org:         |  member_at_org:    | valid token: | expected_status_code:
            # Is the request.user  | Is the Member      | is the token |  The expected
            # associated with the  | associated with    | valid?       |  status code of the
            # Organization?        | the Organization?  |              |  response?
            (True, True, True, 200),
            (True, True, False, 302),
            (False, True, True, 200),
            (False, True, False, 302),
            (True, False, True, 404),
            (True, False, False, 404),
            (False, False, True, 404),
            (False, False, False, 404),
        )
        for (user_at_org, member_at_org, valid_token, expected_status_code) in subtests:
            if user_at_org:
                self.organization.users.add(self.user)
            else:
                self.organization.users.clear()
            if member_at_org:
                self.organization.members.add(self.member)
            else:
                self.organization.members.clear()

            with self.subTest(
                user_at_org=user_at_org,
                member_at_org=member_at_org,
                valid_token=valid_token,
                expected_status_code=expected_status_code
            ):
                token = self.member_token if valid_token else 'not_a_valid_token'
                # Assert that the token is valid or invalid
                if valid_token:
                    self.assertTrue(token_generator.check_token(self.user, token))
                else:
                    self.assertFalse(token_generator.check_token(self.user, token))

                url = reverse(
                    self.url_name,
                    kwargs={
                        'org_slug': self.organization.slug,
                        'username': self.member.user.username,
                        'uidb64': self.member_uid,
                        'token': token
                    }
                )
                response = self.client.get(url)

                if expected_status_code == 200:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['organization'], self.organization)
                    self.assertEqual(response.context['member'], self.member)
                elif expected_status_code == 302:
                    expected_url = reverse(
                        'org:org_create_member_invalid_token',
                        kwargs={
                            'org_slug': self.organization.slug,
                            'username': self.member.user.username
                        }
                    )
                    self.assertRedirects(response, expected_url)
                elif expected_status_code == 404:
                    self.assertEqual(response.status_code, 404)

        with self.subTest(
            'expired token',
            user_at_org=True,
            member_at_org=True,
            expected_status_code=302
        ):
            self.organization.users.add(self.user)
            self.organization.members.add(self.member)

            # Make the token expire
            self.user.set_password('anewpassword123!')
            self.user.save()
            self.assertFalse(token_generator.check_token(self.user, self.member_token))

            response = self.client.get(url)

            # The user should be redirected to the invalid_token page
            expected_url = reverse(
                'org:org_create_member_invalid_token',
                kwargs={'org_slug': self.organization.slug, 'username': self.member.user.username}
            )
            self.assertRedirects(response, expected_url)

    def test_post(self):
        """POSTing to org_create_member_complete view redirects the user to the next step."""
        # The ResourceRequest made from the self.user at the self.organization to
        # access the new Member's data.
        resource_request = ResourceRequestFactory(
            user=self.user,
            organization=self.organization,
            member=self.member.user,
        )
        # The current number of ResourceRequests and ResourceGrants
        expected_num_resource_requests = ResourceRequest.objects.count()
        expected_num_resource_grants = ResourceGrant.objects.count()

        with self.subTest('no data'):
            data = {}
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_user_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {
                    'accept_terms_and_conditions': ['This field is required.'],
                    'give_org_access_to_data': ['This field is required.'],
                    'password1': ['This field is required.'],
                    'password2': ['This field is required.'],
                }
            )
            # No ResourceRequest or ResourceGrant objects have been created
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)
            self.assertEqual(ResourceGrant.objects.count(), expected_num_resource_grants)
            # The ResourceRequest still has a 'Requested' status
            self.assertEqual(resource_request.status, REQUEST_REQUESTED)
            # No requests were made to VMI
            self.assertEqual(self.response_user_detail.call['count'], 0)

        with self.subTest('incomplete data'):
            data = {
                'accept_terms_and_conditions': True,
                'password1': 'password1',
                'password2': 'password1'
            }
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_user_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {'give_org_access_to_data': ['This field is required.']}
            )
            # No ResourceRequest or ResourceGrant objects have been created
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)
            self.assertEqual(ResourceGrant.objects.count(), expected_num_resource_grants)
            # The ResourceRequest still has a 'Requested' status
            self.assertEqual(resource_request.status, REQUEST_REQUESTED)
            # No requests were made to VMI
            self.assertEqual(self.response_user_detail.call['count'], 0)

        with self.subTest('invalid data for BooleanFields'):
            data = {
                'accept_terms_and_conditions': False,
                'give_org_access_to_data': False,
                'password1': 'password1',
                'password2': 'password1'
            }
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_user_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {
                    'accept_terms_and_conditions': ['This field is required.'],
                    'give_org_access_to_data': ['This field is required.'],
                }
            )
            # No ResourceRequest or ResourceGrant objects have been created
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)
            self.assertEqual(ResourceGrant.objects.count(), expected_num_resource_grants)
            # The ResourceRequest still has a 'Requested' status
            self.assertEqual(resource_request.status, REQUEST_REQUESTED)
            # No requests were made to VMI
            self.assertEqual(self.response_user_detail.call['count'], 0)

        with self.subTest('invalid data for passwords'):
            data = {
                'accept_terms_and_conditions': True,
                'give_org_access_to_data': True,
                'password1': 'password1',
                'password2': 'password2',
            }
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_user_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {'password2': ['Passwords must match.']}
            )
            # No ResourceRequest or ResourceGrant objects have been created
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)
            self.assertEqual(ResourceGrant.objects.count(), expected_num_resource_grants)
            # The ResourceRequest still has a 'Requested' status
            self.assertEqual(resource_request.status, REQUEST_REQUESTED)
            # No requests were made to VMI
            self.assertEqual(self.response_user_detail.call['count'], 0)

        with self.subTest('valid data, no request.user UserSocialAuth object'):
            # If the request.user (who is the Member in this test) does not have
            # a UserSocialAuth object for VMI, then the response is an error.
            # In reality, this shouldn't happen, since the UserSocialAuth object
            # should get created for the new Member during step 1 of the member
            # creation process (the org_create_member_view), but we handle the
            # case that the UserSocialAuth object no longer exists.
            data = {
                'accept_terms_and_conditions': True,
                'give_org_access_to_data': True,
                'password1': 'password1',
                'password2': 'password1',
            }

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_user_detail):
                response = self.client.post(self.url, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['errors'],
                {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            )
            # No requests were made to VMI
            self.assertEqual(self.response_user_detail.call['count'], 0)

        with self.subTest(
            'valid data, request.user & member have a UserSocialAuth object, invalid token'
        ):
            # Create a UserSocialAuth object for the self.user for VMI
            UserSocialAuthFactory(
                user=self.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'accessTOKENhere'},
                uid=random.randint(100000000000000, 999999999999999),
            )

            data = {
                'accept_terms_and_conditions': True,
                'give_org_access_to_data': True,
                'password1': 'password1',
                'password2': 'password1',
            }
            url = self.url.replace(self.member_token, 'not_a_valid_token')
            response = self.client.post(url, data=data)

            expected_url_next_page = reverse(
                'org:org_create_member_invalid_token',
                kwargs={
                    'org_slug': self.organization.slug,
                    'username': self.member.user.username
                }
            )
            self.assertRedirects(response, expected_url_next_page)
            # No ResourceRequest or ResourceGrant objects have been created
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)
            self.assertEqual(ResourceGrant.objects.count(), expected_num_resource_grants)
            # The ResourceRequest still has a 'Requested' status
            self.assertEqual(resource_request.status, REQUEST_REQUESTED)
            # No requests were made to VMI
            self.assertEqual(self.response_user_detail.call['count'], 0)

        with self.subTest(
            'valid data, request.user (the member) has a UserSocialAuth object, valid token'
        ):
            # Create a UserSocialAuth object for the Member for VMI
            UserSocialAuthFactory(
                user=self.member.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'MeMbEraccessTOKEN'},
                uid=random.randint(100000000000000, 999999999999999),
            )
            data = {
                'accept_terms_and_conditions': True,
                'give_org_access_to_data': True,
                'password1': 'password1',
                'password2': 'password1',
            }

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_user_detail):
                response = self.client.post(self.url, data=data)

            url_vmi_auth = reverse('social:begin', args=(settings.SOCIAL_AUTH_NAME,))
            url_next_page = reverse(
                'org:org_create_member_success',
                kwargs={
                    'org_slug': self.organization.slug,
                    'username': self.member.user.username
                }
            )
            expected_redirect_url = '{}?next={}'.format(url_vmi_auth, url_next_page)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, expected_redirect_url)
            # No ResourceRequest has been created
            self.assertEqual(ResourceRequest.objects.count(), expected_num_resource_requests)
            # A ResourceGrant object has been created
            expected_num_resource_grants += 1
            self.assertEqual(ResourceGrant.objects.count(), expected_num_resource_grants)
            self.assertEqual(
                ResourceGrant.objects.filter(
                    organization=self.organization,
                    member=self.member.user,
                    resource_request=resource_request,
                ).count(),
                1
            )
            # The ResourceRequest is now approved
            resource_request.refresh_from_db()
            self.assertEqual(resource_request.status, REQUEST_APPROVED)
            # Since we use VMI for authentication, the member's password does not
            # need to be set in smh_app. However, we do so in order to invalidate
            # the self.member_token.
            self.member.user.refresh_from_db()
            self.assertTrue(self.member.user.check_password(data['password1']))
            # A request was made to the user detail API endpoint in VMI
            self.assertEqual(self.response_user_detail.call['count'], 1)

        with self.subTest(
            'valid data, request.user & member have a UserSocialAuth object, expired token'
        ):
            data = {
                'accept_terms_and_conditions': True,
                'give_org_access_to_data': True,
                'password1': 'password1',
                'password2': 'password1',
            }

            # Since the member set their password in the previous subtest, their
            # token has expired.
            self.assertFalse(token_generator.check_token(self.user, self.member_token))

            response = self.client.post(self.url, data=data)

            expected_url_next_page = reverse(
                'org:org_create_member_invalid_token',
                kwargs={
                    'org_slug': self.organization.slug,
                    'username': self.member.user.username
                }
            )
            self.assertRedirects(response, expected_url_next_page)
            # No more requests were made to VMI
            self.assertEqual(self.response_user_detail.call['count'], 1)

    def test_authenticated(self):
        """The user does not need to be authenticated to use the org_create_member_complete view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Authenticated POST'):
            self.client.force_login(self.user)
            response = self.client.post(self.url, data={}, follow=True)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated GET'):
            self.client.logout()

            response = self.client.get(self.url, follow=True)

            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated POST'):
            self.client.logout()

            response = self.client.post(self.url, data={}, follow=True)

            self.assertEqual(response.status_code, 200)


class OrgCreateMemberInvalidTokenTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member_invalid_token'

    def setUp(self):
        super().setUp()
        # An Organization associated with the self.user
        self.organization = OrganizationFactory()
        self.organization.users.add(self.user)
        # A Member at the Organization
        self.member = UserFactory().member
        self.organization.members.add(self.member)
        # The URL for completing new Member creation at the self.organization
        self.url = reverse(
            self.url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username
            }
        )

    def test_get(self):
        """GETting org_create_member_invalid_token view shows a page."""
        subtests = (
            # user_at_org:         |  member_at_org:    | expected_success:
            # Is the request.user  | Is the Member      |  Should the
            # associated with the  | associated with    |  request
            # Organization?        | the Organization?  |  succeed?
            (True, True, True),
            (False, True, True),
            (True, False, False),
            (False, False, False),
        )
        for (user_at_org, member_at_org, expected_success) in subtests:
            organization = OrganizationFactory()
            if user_at_org:
                organization.users.add(self.user)
            member = UserFactory().member
            if member_at_org:
                organization.members.add(member)
            url = reverse(
                self.url_name,
                kwargs={'org_slug': organization.slug, 'username': member.user.username}
            )
            with self.subTest(
                user_at_org=user_at_org,
                member_at_org=member_at_org,
                expected_success=expected_success
            ):
                response = self.client.get(url)

                if expected_success:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['organization'], organization)
                    self.assertEqual(response.context['member'], member)
                else:
                    self.assertEqual(response.status_code, 404)

    def test_authenticated(self):
        """User does not need to be authenticated to use org_create_member_invalid_token view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Authenticated POST'):
            self.client.force_login(self.user)
            response = self.client.post(self.url, data={})
            self.assertEqual(response.status_code, 405)

        with self.subTest('Not authenticated GET'):
            self.client.logout()

            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated POST'):
            self.client.logout()

            response = self.client.post(self.url, data={})

            self.assertEqual(response.status_code, 405)


@override_settings(LOGIN_URL='/accounts/login/')
class OrgCreateMemberSuccessTestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_create_member_success'

    def setUp(self):
        super().setUp()
        # An Organization associated with the self.user
        self.organization = OrganizationFactory()
        self.organization.users.add(self.user)
        # A Member at the Organization
        self.member = UserFactory().member
        self.organization.members.add(self.member)
        # The URL for completing new Member creation at the self.organization
        self.url = reverse(
            self.url_name,
            kwargs={
                'org_slug': self.organization.slug,
                'username': self.member.user.username
            }
        )

    def test_get(self):
        """GETting org_create_member_success view shows a page."""
        subtests = (
            # user_at_org:         |  member_at_org:    | expected_success:
            # Is the request.user  | Is the Member      |  Should the
            # associated with the  | associated with    |  request
            # Organization?        | the Organization?  |  succeed?
            (True, True, True),
            (False, True, True),
            (True, False, False),
            (False, False, False),
        )
        for (user_at_org, member_at_org, expected_success) in subtests:
            organization = OrganizationFactory()
            if user_at_org:
                organization.users.add(self.user)
            member = UserFactory().member
            if member_at_org:
                organization.members.add(member)
            url = reverse(
                self.url_name,
                kwargs={'org_slug': organization.slug, 'username': member.user.username}
            )
            with self.subTest(
                user_at_org=user_at_org,
                member_at_org=member_at_org,
                expected_success=expected_success
            ):
                response = self.client.get(url)

                if expected_success:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['organization'], organization)
                    self.assertEqual(response.context['member'], member)
                else:
                    self.assertEqual(response.status_code, 404)

    def test_authenticated(self):
        """The user does not need to be authenticated to use the org_create_member_complete view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        with self.subTest('Authenticated POST'):
            self.client.force_login(self.user)
            response = self.client.post(self.url, data={})
            self.assertEqual(response.status_code, 405)

        with self.subTest('Not authenticated GET'):
            self.client.logout()

            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)

        with self.subTest('Not authenticated POST'):
            self.client.logout()

            response = self.client.post(self.url, data={})

            self.assertEqual(response.status_code, 405)


@override_settings(LOGIN_URL='/accounts/login/')
class OrgLocalUserAPITestCase(SMHAppTestMixin, TestCase):
    url_name = 'org:org_member_api'

    def test_get(self):
        """GET should return only data for members who are not org agents
        * Users for whom UserProfile.user_type='M'
        * Data is formatted as {'user': ..., 'profile': ..., 'member': ...}.
        * 'user' data should not include password (even hashed)
        """

        # (there's already a self.user whose .userprofile.user_type should default to 'M')
        # add a 'regular' member
        member = UserFactory()
        member.userprofile.user_type = 'M'
        member.userprofile.save()

        # add an org agent
        agent = UserFactory()
        agent.userprofile.user_type = 'O'
        agent.userprofile.save()

        response = self.client.get(reverse(self.url_name))
        data = response.json()
        usernames = [member['user']['username'] for member in data]

        self.assertEqual(len(data), 2)  # self.user + the local member.
        self.assertIn(member.username, usernames)
        self.assertIn(self.user.username, usernames)
        self.assertNotIn(agent.username, usernames)
        for member in data:
            self.assertIn('user', member.keys())
            self.assertIn('profile', member.keys())
            self.assertIn('member', member.keys())
            self.assertNotIn('password', member['user'].keys())
