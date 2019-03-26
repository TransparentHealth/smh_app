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
        client_id = settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY
        client_secret = settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET

        token = self.db_object.access_token
        refresh_url = 'https://alpha.sharemy.health'
        extra = {
            'client_id': client_id,
            'client_secret': client_secret
        }

        def token_saver(token):
            self.db_object.access_token = token
            self.db_object.save()

        client = OAuth2Session(client_id, token=token, auto_refresh_url=refresh_url,
                                                 auto_refresh_kwargs=extra, token_updater=token_saver)
        response = client.get(path)
        return response
