from django.test import TestCase

from .factories import OrganizationFactory


class OrganizationTestCase(TestCase):
    def test_str(self):
        """Test for string representation."""
        organization = OrganizationFactory()
        self.assertEqual(str(organization), organization.name)
