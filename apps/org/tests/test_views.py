from django.test import TestCase
from django.urls import reverse

from .factories import OrganizationFactory, UserFactory
from ..models import Organization


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


class CreateOrganizationTestCase(TestCase):
    url_name = 'org:organization-add'

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


class UpdateOrganizationTestCase(TestCase):
    url_name = 'org:organization-update'

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


class DeleteOrganizationTestCase(TestCase):
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

    def test_update_organizations(self):
        """The user may delete an Organization."""
        # An Organization associated with the self.user
        organization = OrganizationFactory()
        organization.users.add(self.user)

        url = reverse('org:organization-delete', kwargs={'pk': organization.pk})

        response = self.client.post(url)

        self.assertRedirects(response, reverse('org:dashboard'))
        # The Organization has been deleted
        self.assertFalse(Organization.objects.filter(pk=organization.pk).exists())

    def test_update_organization_not_associated(self):
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
