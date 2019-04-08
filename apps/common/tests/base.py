from .factories import UserFactory


class SMHAppTestMixin:
    def setUp(self):
        self.user = UserFactory(username='testuser', email='testuser@example.com')
        self.user.set_password('testpassword')
        self.user.save()
        self.client.force_login(self.user)
