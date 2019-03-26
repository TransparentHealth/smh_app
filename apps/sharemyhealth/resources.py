from django.conf import settings

from requests_oauthlib import OAuth2Session
from social_django.models import UserSocialAuth


class Resource(object):
    """A python wrapper around the social_django.models.UserSocialAuth class."""
    model_class = UserSocialAuth
    # The name matches the model_class's 'provider' field value
    name = 'sharemyhealth'
    # The settings for this resource
    client_id = settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY
    client_secret = settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET

    def __init__(self, user, *args, **kwargs):
        """Set a 'user' and a 'db_object' on the Resource instance."""
        super().__init__(*args, **kwargs)
        # The User who is accessing the self.model_class to get data.
        self.user = user
        # The object in the database that holds the access_token, and the relation
        # to the member.
        self.db_object = self.filter_by_user(user).first()

    def filter_by_user(self, user):
        return self.model_class.objects.filter(user=user, provider=self.name)

    def get(self, path, user, requester=None):
        # get token info for this resource for given user

        token = self.db_object.access_token
        refresh_url = 'https://alpha.sharemy.health'
        extra = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        client = OAuth2Session(
            self.client_id,
            token=token,
            auto_refresh_url=refresh_url,
            auto_refresh_kwargs=extra,
            token_updater=self.token_saver
        )
        response = client.get(path)
        return response

    def token_saver(self, token):
        """Save the token to the self.db_object."""
        self.db_object.access_token = token
        self.db_object.save()
