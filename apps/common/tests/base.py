from io import BytesIO
from httmock import all_requests
from PIL import Image

from apps.org.models import REQUEST_APPROVED
from apps.org.tests.factories import (
    OrganizationFactory, ResourceGrantFactory, ResourceRequestFactory,
    UserSocialAuthFactory
)
from .factories import UserFactory


class SMHAppTestMixin:
    def setUp(self):
        super().setUp()
        self.user = UserFactory(username='testuser', email='testuser@example.com')
        self.user.set_password('testpassword')
        self.user.save()
        self.client.force_login(self.user)

    def get_test_image_for_upload(self, image_mode='RGB', image_format='PNG'):
        """Create a simple test image, in case we need to test uploading an image."""
        img_data = BytesIO()
        size = (100, 100)
        Image.new(image_mode, size).save(img_data, image_format)
        img_data.seek(0)
        return img_data


class MockResourceDataMixin:
    def setUp(self):
        super().setUp()
        # When we mock uses of the requests library, this is the expected mock response.
        self.expected_response_success = {
            'status_code': 200,
            'content': {'test_key': 'Test content'}
        }

    @all_requests
    def response_content_success(self, url, request):
        return self.expected_response_success

    def give_user_access_to_member_token(self, user, member, provider_name):
        """
        Give the user access to the member's access_token, and return access_token.

        This method creates necessary database objects so that the user is in an
        Organization that has a ResourceGrant for the member's Resource, so the
        user can use the member's access_token to get data about the member.
        """
        # The user is a part of an Organization
        organization = OrganizationFactory()
        organization.users.add(user)
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
