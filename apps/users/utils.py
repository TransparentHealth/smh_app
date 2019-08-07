from time import time
import logging
import requests
from django.conf import settings

log = logging.getLogger(__name__)


def refresh_access_token(social_auth):
    log.debug(f'refresh_access_token() {social_auth.user} {social_auth.provider}')
    if 'refresh_token' in social_auth.extra_data:
        refresh_token = social_auth.extra_data['refresh_token']
        provider_upper = social_auth.provider.upper()
        host = getattr(settings, f"SOCIAL_AUTH_{provider_upper}_HOST", None)
        if host:
            refresh_url = f"{host}/o/token/"
            client_id = getattr(settings, f"SOCIAL_AUTH_{provider_upper}_KEY", "")
            client_secret = getattr(settings, f"SOCIAL_AUTH_{provider_upper}_SECRET", "")
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret,
            }
            refresh_response = requests.post(refresh_url, data=refresh_data)
            if refresh_response.status_code == 200:
                log.debug(f"refreshed=True {refresh_response.json()}")
                social_auth.extra_data.update(
                    auth_time=time(),
                    **{
                        k: v
                        for k, v in refresh_response.json().items()
                        if k in ['access_token', 'refresh_token', 'expires_in']
                    },
                )
                social_auth.save()
                return True
