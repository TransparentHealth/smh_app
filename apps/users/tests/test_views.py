import random

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from httmock import remember_called, urlmatch, HTTMock
from social_django.models import UserSocialAuth

from apps.common.tests.base import SMHAppTestMixin
from apps.member.tests.factories import MemberFactory
from apps.org.tests.factories import OrganizationFactory, UserSocialAuthFactory


class UserSettingsViewTestCase(SMHAppTestMixin, TestCase):
    url_name = 'users:user_settings'

    def setUp(self):
        super().setUp()
        self.url = reverse(self.url_name)

    vmi_picture_url = '{}/media/profile-picture/None/no-img.jpg'.format(settings.SOCIAL_AUTH_VMI_HOST)

    @urlmatch(path=r'^/api/v1/user/([0-9]+)?/$')
    @remember_called
    def response_content_success(self, url, request):
        """The response for a successful POST to update a user's settings in VMI."""
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
            'picture': self.vmi_picture_url,
            'preferred_username': username,
            'vot': 'P0.Cc',
            'website': '',
            'address': [],
            'document': []
        }

    def test_get(self):
        """GETting the user_settings view shows a form to update the user's settings."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """POSTing to the user_settings view can update a user's picture URL."""
        with self.subTest('no data'):
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_content_success):
                response = self.client.post(self.url, {'picture': None})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {'picture': ['This field is required.']}
            )
            # The self.user's UserProfile was not updated
            self.user.userprofile.refresh_from_db()
            self.assertEqual(self.user.userprofile.picture_url, '')
            # No requests were made to VMI
            self.assertEqual(self.response_content_success.call['count'], 0)

        with self.subTest('invalid data'):
            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_content_success):
                response = self.client.post(self.url, {'picture': 'not a valid image'})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['form'].errors,
                {'picture': ['This field is required.']}
            )
            # The self.user's UserProfile was not updated
            self.user.userprofile.refresh_from_db()
            self.assertEqual(self.user.userprofile.picture_url, '')
            # No requests were made to VMI
            self.assertEqual(self.response_content_success.call['count'], 0)

        with self.subTest('valid data, no request.user UserSocialAuth object'):
            # If the request.user does not have a UserSocialAuth object for VMI,
            # then the response is an error.

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            test_image = self.get_test_image_for_upload()
            with HTTMock(self.response_content_success):
                response = self.client.post(
                    self.url,
                    {'picture': SimpleUploadedFile('picture.png', test_image.getvalue())}
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context['errors'],
                {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            )

            # The self.user's UserProfile was not updated
            self.user.userprofile.refresh_from_db()
            self.assertEqual(self.user.userprofile.picture_url, '')
            # No requests were made to VMI
            self.assertEqual(self.response_content_success.call['count'], 0)

        with self.subTest('valid data, request.user has a UserSocialAuth object'):
            # Create a UserSocialAuth object for the self.user for VMI
            UserSocialAuthFactory(
                user=self.user,
                provider=settings.SOCIAL_AUTH_NAME,
                extra_data={'refresh_token': 'refreshTOKEN', 'access_token': 'accessTOKENhere'},
                uid=random.randint(100000000000000, 999999999999999),
            )

            test_image = self.get_test_image_for_upload()

            # Since POSTs with valid data use the requests library to make a request
            # to the settings.SOCIAL_AUTH_VMI_HOST URL, mock uses of the requests
            # library here.
            with HTTMock(self.response_content_success):
                response = self.client.post(
                    self.url, {'picture': SimpleUploadedFile('picture.png', test_image.getvalue())}
                )

            # A successful create redirects to the next page of the creation process.
            self.assertEqual(response.status_code, 200)
            # The self.user's UserProfile was updated
            self.user.userprofile.refresh_from_db()
            self.assertEqual(self.user.userprofile.picture_url, self.vmi_picture_url)
            # One request was made to VMI
            self.assertEqual(self.response_content_success.call['count'], 1)

    def test_authenticated(self):
        """The user must be authenticated to use the user_settings view."""
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


class UserMemberRouterTestCase(SMHAppTestMixin, TestCase):
    url_name = 'users:user_member_router'

    def setUp(self):
        super().setUp()
        self.url = reverse(self.url_name)

    def test_get_post(self):
        """
        GETting or POSTing the user_member_router redirects the user, based on who the User is:
         - if the request.user is an Organization User, the User is redirected to the org dashboard
         - if the request.user is a member, the User is redirected to the member dashboard
         - otherwise, the User is redirected to the org dashboard
        """

        subtests = (
            # has_org             | has_member  | member_has_org             | expected_redirect
            # Does the            | Does the    | Does the request.user's    | The url_name that
            # request.user have   | request.user| Member have an association | the user should
            # an association with | have a      | with an Organization?      | be redirected to
            # an Organization?    | Member?     |                            |
            (True,                    False,         False,                    'org:dashboard'),
            (True,                    True,          False,                    'org:dashboard'),
            (True,                    True,          True,                     'org:dashboard'),

            (False,                   True,          False,                    'member:dashboard'),
            (False,                   True,          True,                     'member:dashboard'),
            (False,                   False,         False,                    'org:dashboard'),
        )

        for (has_org, has_member, member_has_org, expected_redirect) in subtests:
            for method_name in ['get', 'post']:
                with self.subTest(
                    method_name=method_name,
                    has_org=has_org,
                    has_member=has_member,
                    member_has_org=member_has_org,
                    expected_redirect=expected_redirect,
                ):
                    self.user.refresh_from_db()

                    if has_org:
                        organization = OrganizationFactory()
                        organization.users.add(self.user)
                    else:
                        self.user.organization_set.clear()

                    if has_member:
                        if not hasattr(self.user, 'member'):
                            self.user.member = MemberFactory(user=self.user)
                        if member_has_org:
                            organization = OrganizationFactory()
                            organization.members.add(self.user.member)
                        else:
                            self.user.member.organizations.clear()
                    elif not has_member and hasattr(self.user, 'member'):
                        self.user.member.delete()

                    # Use the relevant method (GET or POST).
                    method = getattr(self.client, method_name)
                    response = method(self.url)

                    self.assertRedirects(response, reverse(expected_redirect))

    def test_authenticated(self):
        """The user must be authenticated to use the user_member_router view."""
        with self.subTest('Authenticated GET'):
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 302)

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
