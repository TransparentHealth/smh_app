from unittest import mock

from django.test import TestCase
from django.utils.text import slugify

from .factories import OrganizationFactory, ResourceGrantFactory, ResourceRequestFactory


class OrganizationTestCase(TestCase):
    def test_str(self):
        """Test for string representation."""
        organization = OrganizationFactory()
        self.assertEqual(str(organization), organization.name)

    def test_saving_without_slug_creates_unique_slug(self):
        """Saving a new Organization without a slug gives it a unique slug based on its name."""
        with self.subTest('new Organization with slug'):
            # Saving an Organization and specifyung its slug gives it that slug
            organization = OrganizationFactory(slug='explicit-slug')
            self.assertEqual(organization.slug, 'explicit-slug')

        with self.subTest('new Organization without slug'):
            # Saving an Organization without a slug gives it a slug based on its name
            name = 'New Organization'
            slugified_name = slugify(name)
            organization = OrganizationFactory(name=name, slug='')
            self.assertEqual(organization.slug, slugified_name)

        with self.subTest('new Organization without slug, with same slugified name'):
            # Saving an Organization without a slug, when another Organization exists
            # that already has what would be the new Organization's slugified name as
            # its slug, still creates a unique slug based on the Organization's name.
            name = 'New Organization!'
            slugified_name = slugify(name)
            organization = OrganizationFactory(name=name, slug='')

            self.assertNotEqual(organization.slug, '')
            self.assertIn(slugified_name, organization.slug)

        with self.subTest('old Organization without slug'):
            # Saving an Organization that already exists to have an empty slug
            # sets the slug to empty string.
            organization.slug = ''
            organization.save()
            self.assertEqual(organization.slug, '')


class ResourceGrantTestCase(TestCase):
    def test_str(self):
        """Test for string representation."""
        org_resource_access = ResourceGrantFactory()
        self.assertEqual(
            str(org_resource_access),
            "{} access to {} for {}".format(
                org_resource_access.organization,
                org_resource_access.provider_name,
                org_resource_access.member
            )
        )

    @mock.patch('apps.sharemyhealth.resources.Resource')
    def test_resource_class(self, mock_resource_class):
        """
        The resource_class property is the class that the resource_class_path refers to.

        Note: since we mock the apps.sharemyhealth.resources.Resource class, that
        will be this test's ResourceGrant's resource_class_path.
        """
        resource_grant = ResourceGrantFactory(
            resource_class_path='apps.sharemyhealth.resources.Resource'
        )

        self.assertEqual(resource_grant.resource_class, mock_resource_class)

    @mock.patch('apps.sharemyhealth.resources.Resource')
    def test_provider_name(self, mock_resource_class):
        """
        The provider_name property should be the resource_class's name.

        Note: since we mock the apps.sharemyhealth.resources.Resource class, that
        will be this test's ResourceGrant's resource_class_path, so we can assert
        that its name really is returned as the ResourceRequest's provider_name.
        """
        test_resource_class_name = 'testclassname'
        mock_resource_class.name = test_resource_class_name

        resource_grant = ResourceGrantFactory(
            resource_class_path='apps.sharemyhealth.resources.Resource'
        )

        self.assertEqual(resource_grant .provider_name, test_resource_class_name)


class ResourceRequestTestCase(TestCase):
    def test_str(self):
        """Test for string representation."""
        resource_request = ResourceRequestFactory()
        self.assertEqual(
            str(resource_request),
            "Request by {} for access to {} for {}".format(
                resource_request.organization,
                resource_request.provider_name,
                resource_request.member
            )
        )

    @mock.patch('apps.sharemyhealth.resources.Resource')
    def test_resource_class(self, mock_resource_class):
        """
        The resource_class property is the class that the resource_class_path refers to.

        Note: since we mock the apps.sharemyhealth.resources.Resource class, that
        will be this test's ResourceGrant's resource_class_path.
        """
        resource_request = ResourceRequestFactory(
            resource_class_path='apps.sharemyhealth.resources.Resource'
        )

        self.assertEqual(resource_request.resource_class, mock_resource_class)

    @mock.patch('apps.sharemyhealth.resources.Resource')
    def test_provider_name(self, mock_resource_class):
        """
        The provider_name property should be the resource_class's name.

        Note: since we mock the apps.sharemyhealth.resources.Resource class, that
        will be this test's ResourceRequest's resource_class, so we can assert
        that its name really is returned as the ResourceRequest's provider_name.
        """
        test_resource_class_name = 'testclassname'
        mock_resource_class.name = test_resource_class_name

        resource_request = ResourceRequestFactory(
            resource_class_path='apps.sharemyhealth.resources.Resource'
        )

        self.assertEqual(resource_request.provider_name, test_resource_class_name)
