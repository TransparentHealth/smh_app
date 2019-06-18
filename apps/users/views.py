import json
import requests
from urllib.parse import urlparse
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, reverse, render
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect
from .forms import UserSettingsForm
from .models import UserProfile
from django.contrib import messages
from django.contrib.auth import logout
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger('smhapp_.%s' % __name__)


def mylogout(request):
    if request.user.is_authenticated:
        logger.info("%s %s logged out.", request.user.first_name,
                request.user.last_name)
        logout(request)
        messages.success(request, _('You have been logged out.'))
    return HttpResponseRedirect(reverse('home'))


def authenticated_home(request):

    if request.user.is_authenticated:
        up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
        if up.user_type == "O":

            return HttpResponseRedirect(reverse('org:dashboard'))
        return HttpResponseRedirect(reverse('member:dashboard'))
    return render(request, 'homepage.html', {'SOCIAL_AUTH_NAME': settings.SOCIAL_AUTH_NAME})


class UserSettingsView(LoginRequiredMixin, FormView):
    """A view for allowing a User to change their user settings."""
    template_name = 'users/user_settings.html'
    form_class = UserSettingsForm
    login_url = 'home'
    # If there are any non-form errors, they can be stored in self.errors, and
    # will be displayed in the template.
    errors = {}

    def get_context_data(self, **kwargs):
        """Get the context data for the template."""
        kwargs.setdefault('errors', self.errors)
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        """
        If the form is valid, then:
         1.) verify that the request.user has a UserSocialAuth object for VMI
         2.) make a request to VMI to update the user's profile picture in VMI
         3.) update the user's UserProfile's picture_url
         4.) render the user settings page to the user
        """
        # 1.) Verify that the request.user has a UserSocialAuth object for VMI
        request_user_social_auth = self.request.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the request.user does not have a UserSocialAuth for VMI, then
        # return the error to the user.
        if not request_user_social_auth:
            self.errors = {
                'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)
            }
            return self.render_to_response(self.get_context_data())

        # 2.) Make a request to VMI to update the user's profile picture in VMI
        url = '{}/api/v1/user/{}/'.format(settings.SOCIAL_AUTH_VMI_HOST,
                                          request_user_social_auth.uid)
        files = {'picture': self.request.FILES.get('picture')}
        headers = {'Authorization': "Bearer {}".format(
            request_user_social_auth.access_token)}
        response = requests.post(url, files=files, headers=headers)

        # 3.) Update a user's UserProfile with the response from VMI.
        # If the request successfully updated a user in VMI, then use that data
        # to update the UserProfile in smh_app. If not, then show the error to
        # the user.
        if response.status_code == 200:
            response_data_dict = json.loads(response.content)
            parsed_url = urlparse(response_data_dict['picture'])
            # Update the UserProfile
            self.request.user.userprofile.picture_url = "{}{}".format(
                settings.SOCIAL_AUTH_VMI_HOST,
                parsed_url.path
            )
            self.request.user.userprofile.save()
        else:
            # The request to update a user in VMI did not succeed, so show
            # errors to the user.
            self.errors = json.loads(response.content)

        # 4.) Render the user settings page to the user
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


@login_required(login_url='home')
def user_member_router(request):
    """
    Redirect the user, based on which type of user they are:
     - if the request.user is an Organization User, redirect to the org dashboard
     - if the request.user is a member, redirect to the member dashboard
     - otherwise, redirect to the org dashboard
    """
    # If the request.user is an Organization User, then redirect to the org
    # dashboard
    if request.user.organization_set.exists():
        return redirect(reverse('org:dashboard'))

    # If the request.user is a Member, then redirect to the member dashboard
    if hasattr(request.user, 'member'):
        return redirect(reverse('member:dashboard'))

    # The request.user is not associated with any Organizations, and is not a Member.
    # Redirect to the org dashboard (in case this is an Organization User who is
    # being set up).
    return redirect(reverse('org:dashboard'))
