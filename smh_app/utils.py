import requests

from smh_app.settings import SOCIAL_AUTH_VMI_HOST


def get_vmi_user_data(request):
    """ Makes a call to the VMI user_profile endpoint and returns a response """
    user_endpoint = SOCIAL_AUTH_VMI_HOST + '/api/v1/user/'
    social_auth_extra_data = request.user.social_auth.values().first()['extra_data']
    token = social_auth_extra_data['access_token'] if social_auth_extra_data else None
    response = requests.get(
        url=user_endpoint,
        headers={'Authorization': "Bearer {}".format(token)}
    )
    return response
