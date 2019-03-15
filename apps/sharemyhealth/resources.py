from social_django.models import UserSocialAuth


class Resource(object):
    """A python wrapper around the social_django.models.UserSocialAuth class."""
    model_class = UserSocialAuth
    # The name matches the model_class's 'provider' field value
    name = 'sharemyhealth'

    def filter_by_user(self, user):
        return self.model_class.objects.filter(user=user, provider=self.name)
