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
    # The URL to use when GETting the data
    url_for_data = 'https://alpha.sharemy.health/'
    # The URL to refresh the token
    url_token_refresh = 'https://alpha.sharemy.health'

    def __init__(self, member, *args, **kwargs):
        """Set a 'member' and a 'db_object' on the Resource instance."""
        super().__init__(*args, **kwargs)
        # The member whose token from the self.model_class will be used to get data.
        self.member = member
        # The object in the database that holds the access_token, and the relation
        # to the member.
        self.db_object = self.filter_by_user(member).first()

    def filter_by_user(self, member):
        return self.model_class.objects.filter(user=member, provider=self.name)

    def get(self):
        """GET the data from the self.url_for_data."""
        # A dictioary of token data for this resource
        token_dict = {
            'access_token': self.db_object.access_token,
            'refresh_token': self.db_object.extra_data['refresh_token'],
            'token_type': 'Bearer',
            'expires_in': '3600',
        }
        # Other data sent as a part of the request
        extra = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        client = OAuth2Session(
            self.client_id,
            token=token_dict,
            auto_refresh_url=self.url_token_refresh,
            auto_refresh_kwargs=extra,
            token_updater=self.token_saver
        )
        response = client.get(self.url_for_data)
        return response

    def token_saver(self, token):
        """Save the token to the self.db_object."""
        self.db_object.access_token = token
        self.db_object.save()
