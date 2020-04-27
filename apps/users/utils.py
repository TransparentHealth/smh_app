import logging
from time import time

import requests
from django.conf import settings
from jwkest.jwt import JWT

log = logging.getLogger(__name__)


def get_id_token_payload(user):
    # Get the ID Token and parse it, return a JSON string.
    try:
        provider = user.social_auth.filter(provider='verifymyidentity-openidconnect').first()
        if 'id_token' in provider.extra_data.keys():
            id_token = provider.extra_data.get('id_token')
            parsed_id_token = JWT().unpack(id_token).payload()
        else:
            parsed_id_token = {'sub': '', 'ial': '1'}

    except Exception:
        parsed_id_token = {'sub': '', 'ial': '1'}

    return parsed_id_token


def refresh_access_token(social_auth):
    log.debug(f'refresh_access_token() {social_auth.user} {social_auth.provider}')
    if 'refresh_token' in social_auth.extra_data:
        refresh_token = social_auth.extra_data['refresh_token']
        provider_upper = social_auth.provider.upper()
        host = getattr(settings, f"SOCIAL_AUTH_{provider_upper}_HOST", None)
        if host:
            refresh_url = f"{host}/o/token/"
            client_id = getattr(settings, f"SOCIAL_AUTH_{provider_upper}_KEY", "")
            client_secret = getattr(
                settings, f"SOCIAL_AUTH_{provider_upper}_SECRET", ""
            )
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
