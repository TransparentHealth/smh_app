from django.conf import settings

from social_core.backends.oauth import BaseOAuth2


class VMIOAuth2Backend(BaseOAuth2):
    """A backend for authenticating to VerifyMyIdentity (VMI)."""
    name = getattr(settings, 'SOCIAL_AUTH_VMI_NAME')
    SOCIAL_AUTH_VMI_HOST = getattr(settings, 'SOCIAL_AUTH_VMI_HOST')
    ID_KEY = 'email'
    AUTHORIZATION_URL = SOCIAL_AUTH_VMI_HOST + '/o/authorize/'
    ACCESS_TOKEN_URL = SOCIAL_AUTH_VMI_HOST + '/o/token/'

    def get_user_profile_url(self):
        """
        Return the url to the user profile endpoint.
        """
        user_profile_url = getattr(settings, 'SOCIAL_AUTH_VMI_HOST') + '/userprofile'
        return user_profile_url

    def get_user_id(self, details, response):
        # Extracts the user id from `user_data` response.
        return response.get(self.ID_KEY)

    def get_user_details(self, response):
        """Return user details from response."""
        return {
            'username': response.get('sub'),
            'first_name': response.get('given_name'),
            'last_name': response.get('family_name'),
            'email': response.get('email'),
            'patient': response.get('patient'),
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service."""
        return self.get_json(
            self.get_user_profile_url(),
            params={'access_token': access_token}
        )
