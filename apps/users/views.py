import logging

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, reverse
from django.utils.translation import ugettext_lazy as _
from requests_oauthlib import OAuth2Session
from social_django.models import UserSocialAuth

from apps.users.utils import refresh_access_token

logger = logging.getLogger('smhapp_.%s' % __name__)


def mylogout(request):
    if request.user.is_authenticated:
        try:
            # Attempt a remote logout.
            social = request.user.social_auth.get(
                provider='verifymyidentity-openidconnect')
            token = social.extra_data['access_token']
            oas = OAuth2Session(token=token)
            oas.access_token = token
            remote_logout = settings.REMOTE_LOGOUT_ENDPOINT
            response = oas.get(remote_logout)
            print(response.status_code, response.content)
            if response.status_code in [401, 403]:
                refreshed = refresh_access_token(social)
                if refreshed:
                    token = social.extra_data['access_token']
                    oas = OAuth2Session(token=token)
                    oas.access_token = token
                    response = oas.get(remote_logout)
                    print(response.status_code, response.content)

            logger.info(
                _("%s remote logout of %s")
                % (request.user, settings.REMOTE_LOGOUT_ENDPOINT)
            )
        except UserSocialAuth.DoesNotExist:
            pass
        logger.info(_("$s logged out."), request.user)
        logout(request)
    # messages.success(request, _('You have been logged out.'))
    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return HttpResponseRedirect(reverse('home'))


def authenticated_home(request):
    if request.user.is_authenticated:
        return user_router(request)
    else:
        return render(
            request, 'homepage.html', {}
        )


@login_required(login_url='home')
def user_router(request):
    """
    Redirect the user, based on which type of user they are:
     - if the request.user is an Organization User, redirect to the org dashboard
     - if the request.user is a member, redirect to the member dashboard
     - otherwise, redirect to the org dashboard
    """
    # If the request.user is an Organization Agent, then redirect to the org
    # dashboard
    if request.user.agent_organizations.exists():
        return redirect(reverse('org:dashboard'))

    # Otherwise, redirect to the member dashboard
    else:
        return redirect(reverse('member:dashboard'))
