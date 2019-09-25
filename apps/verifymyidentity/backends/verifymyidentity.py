from social_core.backends.open_id_connect import OpenIdConnectAuth

__author__ = "Alan Viars"


class VerifyMyIdentityOpenIdConnect(OpenIdConnectAuth):
    name = 'verifymyidentity-openidconnect'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.OIDC_ENDPOINT = self.setting('SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_HOST',
                                          '')
