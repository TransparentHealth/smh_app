from django.conf import settings

from requests_oauthlib import OAuth2Session
from social_django.models import UserSocialAuth


class Resource(object):
    """A python wrapper around the social_django.models.UserSocialAuth class."""
    model_class = UserSocialAuth
    # The name matches the model_class's 'provider' field value
    name = 'sharemyhealth'

    def filter_by_user(self, user):
        return self.model_class.objects.filter(user=user, provider=self.name)

    def get(self, path, user, requester=None):
        # get token info for this resource for given user
        client_id = settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY
        client_secret = settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET

        db_object = self.filter_by_user(user).first()
        token = db_object.access_token
        refresh_url = 'https://alpha.sharemy.health'
        extra = {
            'client_id': client_id,
            'client_secret': client_secret
        }

        def token_saver(token):
            db_object.access_token = token
            db_object.save()

        client = OAuth2Session(client_id, token=token, auto_refresh_url=refresh_url,
                                                 auto_refresh_kwargs=extra, token_updater=token_saver)
        response = client.get(path)
        return response
