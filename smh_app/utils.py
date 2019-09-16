from decimal import Decimal

import requests
from django.conf import settings

TRUE_LIST = [1, "1", "true", "True", "TRUE", "YES", "Yes", "yes", True]
FALSE_LIST = [0, "0", "False", "FALSE", "false", "NO", "No", "no", False]


def bool_env(env_val):
    """ check for boolean values """

    if env_val:
        if env_val in TRUE_LIST:
            return True
        if env_val in FALSE_LIST:
            return False
        return env_val
    else:
        if env_val in FALSE_LIST:
            return False
        return


def int_env(env_val):
    """ convert to integer from String """

    return int(Decimal(float(env_val)))


def get_vmi_user_data(request):
    """ Makes a call to the VMI user_profile endpoint and returns a response """
    user_endpoint = settings.SOCIAL_AUTH_VMI_HOST + '/api/v1/user/'
    social_auth_extra_data = request.user.social_auth.values().first()['extra_data']
    token = social_auth_extra_data['access_token'] if social_auth_extra_data else None
    response = requests.get(
        url=user_endpoint, headers={'Authorization': "Bearer {}".format(token)}
    )
    return response
