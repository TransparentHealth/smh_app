from django.test import TestCase
from django.utils.text import slugify

from .factories import OrganizationFactory


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
