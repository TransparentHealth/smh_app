from django.test import TestCase
from django.urls import reverse

from .factories import OrganizationFactory, UserFactory


class OrganizationDashboardTestCase(TestCase):
    url_name = 'org:dashboard'

    def setUp(self):
        self.user = UserFactory(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user.set_password('testpassword')
        self.user.save()
        self.client.force_login(self.user)

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
