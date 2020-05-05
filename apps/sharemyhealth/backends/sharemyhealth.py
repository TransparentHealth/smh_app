from django.conf import settings
from social_core.backends.open_id_connect import OpenIdConnectAuth

__author__ = "Alan Viars"

# Videntity Systems Inc.


class ShareMyHealthOAuth2Backend(OpenIdConnectAuth):
    """
    This is not an OIDC endpoint but we are using the discovery.
    TODO: Get the OAUTH2 discovery instead....more to standard.
    """

    name = "sharemyhealth"
    
    # http://openid.net/specs/openid-connect-core-1_0.html#rfc.section.15.6.2

    DEFAULT_SCOPE = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.OIDC_ENDPOINT =  settings.SOCIAL_AUTH_SHAREMYHEALTH_HOST
        self.REVOKE_TOKEN_METHOD = "POST"  # Just set for documentation

        # Note the ending slash must be present for this POST
        self.REVOKE_TOKEN_URL = "%s%s" % (
            settings.SOCIAL_AUTH_SHAREMYHEALTH_HOST, "/o/revoke_token/")

    def request_access_token(self, *args, **kwargs):
        """
        Retrieve the access token.

        Since ShareMyHealth doesn't return an id_token, we override this method
        to remove the id_token validation.
        """
        return self.get_json(*args, **kwargs)
