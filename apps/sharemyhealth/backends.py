from django.conf import settings
from social_core.backends.open_id_connect import OpenIdConnectAuth


class ShareMyHealthOAuth2Backend(OpenIdConnectAuth):
    """
    An OAuth backend, similar to what is used in sharemyhealth repo.

    For reference, the sharemyhealth use is: https://github.com/TransparentHealth/
    sharemyhealth/blob/master/apps/verifymyidentity/authentication.py.
    """

    name = "sharemyhealth"

    # differs from value in discovery document
    # http://openid.net/specs/openid-connect-core-1_0.html#rfc.section.15.6.2

    DEFAULT_SCOPE = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.OIDC_ENDPOINT = getattr(settings, 'SOCIAL_AUTH_SHAREMYHEALTH_HOST')

    def request_access_token(self, *args, **kwargs):
        """
        Retrieve the access token.

        Since ShareMyHealth doesn't return us an id_token, we override this method
        to remove the id_token validation.
        """
        return self.get_json(*args, **kwargs)
