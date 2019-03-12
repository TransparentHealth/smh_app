from social_django.models import UserSocialAuth


class Resource(object):
    """A python wrapper around the social_django.models.UserSocialAuth class."""
    model_class = UserSocialAuth

    def filter_by_user_and_provider(self, user, provider):
        return self.model_class.objects.filter(user=user, provider=provider)
