from django.test import TestCase, override_settings
from django.urls import reverse
from apps.common.tests.base import SMHAppTestMixin
from apps.common.tests.factories import UserFactory
from apps.notifications.models import Notification
from apps.org.tests.factories import OrganizationFactory


@override_settings(LOGIN_URL='/accounts/login/')
class DismissNotificationTestCase(SMHAppTestMixin, TestCase):
    url_name = 'notifications:dismiss'

    def setUp(self):
        super().setUp()
        self.notification = Notification.objects.create(
            notify=self.user, actor=self.user, message="Notify Me")

    def test_post_user_valid(self):
        """dismissing a notification for self.user results in that Notification.dismissed=True"""
        self.assertFalse(self.notification.dismissed)
        response = self.client.post(
            reverse('notifications:dismiss', kwargs={'pk': self.notification.pk}))
        self.notification.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.notification.dismissed)

    def test_post_invalid(self):
        """posting dismissal with out-of-range (non-positive) pk results in status = 422"""
        response = self.client.post(reverse('notifications:dismiss', kwargs={'pk': '0'}))
        self.assertEqual(response.status_code, 422)

    def test_post_nonexistent(self):
        """posting dismissal of a non-existent Notification raises 404"""
        notification = Notification.objects.create(
            notify=self.user, actor=self.user, message="Notify Me")
        pk = notification.pk
        notification.delete()

        response = self.client.post(reverse('notifications:dismiss', kwargs={'pk': pk}))
        self.assertEqual(response.status_code, 404)

    def test_post_user_unauthorized(self):
        """posting dismissal of another user's notification raises 404"""
        other_user = UserFactory()
        notification = Notification.objects.create(
            notify=other_user, actor=self.user, message="Notify Other User")
        pk = notification.pk

        response = self.client.post(reverse('notifications:dismiss', kwargs={'pk': pk}))

        self.assertEqual(response.status_code, 404)

    def test_post_org_valid(self):
        """posting dismissal of a notification to an org that the user is an agent for works"""
        org = OrganizationFactory()
        org.users.add(self.user)
        notification = Notification.objects.create(notify=org, actor=self.user, message="Notify Us")

        response = self.client.post(
            reverse('notifications:dismiss', kwargs={'pk': notification.pk}))
        notification.refresh_from_db()

        self.assertTrue(notification.dismissed)

    def test_post_org_unauthorized(self):
        """posting dismissal of an org notification that the user is not an agent of returns 404"""
        org = OrganizationFactory()
        notification = Notification.objects.create(
            notify=org, actor=self.user, message="Notify the Org")

        response = self.client.post(
            reverse('notifications:dismiss', kwargs={'pk': notification.pk}))

        self.assertEqual(response.status_code, 404)
