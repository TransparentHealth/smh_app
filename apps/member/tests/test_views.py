from django.test import TestCase
from django.urls import reverse

from apps.common.tests.base import SMHAppTestMixin
from apps.org.tests.factories import ResourceRequestFactory
from apps.org.models import Organization


class MemberDashboardTestCase(SMHAppTestMixin, TestCase):
    url_name = 'member:dashboard'

    def test_member_dashboard(self):
        """GETting member dashboard shows ResourceRequests for request.user's resources."""
        # Some ResourceRequests for the request.user
        expected_resource_request_ids = [
            ResourceRequestFactory(member=self.user).id for i in range(0, 3)
        ]
        # Some ResourceRequests for other users
        for i in range(0, 2):
            ResourceRequestFactory()

        response = self.client.get(reverse(self.url_name))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context_data['resource_requests'].values_list('id', flat=True)),
            set(expected_resource_request_ids)
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
