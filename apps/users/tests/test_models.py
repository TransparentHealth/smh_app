from django.test import TestCase

from apps.common.tests.factories import UserFactory


class UserProfileTestCase(TestCase):
    def test_str(self):
        """Test for string representation."""
        user = UserFactory()
        self.assertEqual(str(user.username), user.username)
