import json
import uuid

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from social_django.models import UserSocialAuth

from apps.notifications.models import Notification
from apps.users.utils import refresh_access_token
from libs.qrcode import make_qr_code

from .forms import (
    CreateNewMemberAtOrgForm,
    UpdateNewMemberAtOrgAdditionalInfoForm,
    UpdateNewMemberAtOrgBasicInfoForm,
    UpdateNewMemberAtOrgMemberForm,
    VerifyMemberIdentityForm,
)
from .models import (
    REQUEST_APPROVED,
    REQUEST_REQUESTED,
    RESOURCE_CHOICES,
    Organization,
    ResourceGrant,
    ResourceRequest,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "org/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add the user's Organizations, to the context."""
        # All of the Organizations that the request.user is a part of -- i.e.,
        # is an agent in
        context = super().get_context_data(**kwargs)
        context['orgs_with_members'] = [
            {
                'organization': org,
                'members': [rg.member for rg in org.resource_grants.all()],
                'notifications': Notification.objects.filter(
                    notify_id=org.id, dismissed=False
                ).order_by('-created')[:4],
            }
            for org in self.request.user.agent_organizations.all()
        ]

        return context


class OrgCreateMemberMixin:
    """A mixin for the create member views."""

    def get_organization(self, request, org_slug):
        """Get the Organization object that the org_slug refers to, or return a 404 response."""
        return get_object_or_404(
            Organization.objects.filter(agents=request.user), slug=org_slug
        )

    def get_member(self, organization, username):
        """Get the Member object that the username refers to, or return a 404 response."""
        return get_object_or_404(
            get_user_model().objects.filter(member_organizations=organization),
            username=username,
        )

    def get_context_data(self, **kwargs):
        """Get the context data for the template."""
        kwargs.setdefault('organization', self.organization)
        kwargs.setdefault('member', self.member)
        kwargs.setdefault('errors', self.errors)
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        """Set the self.organization and self.member."""
        self.organization = self.get_organization(
            request, self.kwargs.get('org_slug'))
        self.member = self.get_member(
            self.organization, self.kwargs.get('username'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Set the self.organization and self.member."""
        self.organization = self.get_organization(
            request, self.kwargs.get('org_slug'))
        self.member = self.get_member(
            self.organization, self.kwargs.get('username'))
        return super().post(request, *args, **kwargs)


class OrgCreateMemberView(LoginRequiredMixin, OrgCreateMemberMixin, FormView):
    """A view for allowing an organization agent to create a member for that Organization."""

    template_name = 'org/org_create_member.html'
    form_class = CreateNewMemberAtOrgForm
    login_url = 'home'
    # If there are any non-form errors, they can be stored in self.errors, and
    # will be displayed in the template.
    errors = {}

    def get_success_url(self, org_slug, username):
        """A successful creation redirects to the next step in the process."""
        return reverse(
            'org:org_create_member_basic_info',
            kwargs={'org_slug': org_slug, 'username': username},
        )

    def get_member(self, organization, username):
        """Override the get_member() method, since the Member does not yet exist."""
        return None

    def form_valid(self, form):
        """
        If the form is valid, then create the new member:
         1.) Verify that the request.user has a UserSocialAuth object for VMI
         2.) make a request to VMI to create the new user in VMI
         3.) create a new Member with the response from VMI
         4.) create a ResourceRequest for the new Member's data from the relevant Organization
         5.) redirect the user to the next step in the Member-creation process
        """
        # 1.) Verify that the request.user has a UserSocialAuth object for VMI
        request_user_social_auth = self.request.user.social_auth.filter(
            provider='verifymyidentity-openidconnect'
        ).first()
        # If the request.user does not have a UserSocialAuth for VMI, then
        # return the error to the user.
        if not request_user_social_auth:
            self.errors = {
                'user': 'User has no association with {}'.format(
                    'verifymyidentity-openidconnect'
                )
            }
            return self.render_to_response(self.get_context_data())

        # 2.) Make a request to VMI to create the new user
        # The data to be POSTed to VMI
        data = {
            # required form data, so we know it's present and cleaned
            'given_name': form.cleaned_data['first_name'],
            'family_name': form.cleaned_data['last_name'],
            'preferred_username': form.cleaned_data['username'],
            # non-required form data, might not be present
            'phone_number': form.cleaned_data.get('phone_number', 'none').strip(),
            # The following fields are required by VMI, but we don't have values
            # for them yet, so we make up some data now, and require the user
            # to fill them in during the next steps of the Member creation
            # process.
            'gender': '',  # = Unspecified
            'password': str(uuid.uuid4()),
            'birthdate': '2000-01-01',
            'nickname': form.cleaned_data['first_name'],
            'email': form.cleaned_data.get('email', ''),
        }
        # POST the data to VMI
        url = settings.SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_HOST + '/api/v1/user/'
        headers = {
            'Authorization': "Bearer {}".format(request_user_social_auth.access_token)
        }
        response = requests.post(url=url, data=data, headers=headers)
        if response.status_code in [401, 403]:
            refreshed = refresh_access_token(request_user_social_auth)
            if refreshed:  # repeat the previous request
                headers = {
                    'Authorization': "Bearer {}".format(
                        request_user_social_auth.access_token
                    )
                }
                response = requests.post(url=url, data=data, headers=headers)

        # 3.) Create a new Member with the response from VMI.
        # If the request successfully created a user in VMI, then use that data
        # to create a Member that is linked to the VMI user through a
        # UserSocialAuth.
        if response.status_code == 201:
            response_data_dict = json.loads(response.content)
            # Create the Member, and associate with this Organization
            print("RESPONSE", response_data_dict)
            new_user = get_user_model().objects.create(
                first_name=response_data_dict['given_name'],
                last_name=response_data_dict['family_name'],
                email=response_data_dict['email'],
                username=response_data_dict['sub'],
            )

            # Create a UserSocialAuth for the new Member
            UserSocialAuth.objects.create(
                user_id=new_user.id, provider='verifymyidentity-openidconnect',
                uid=response_data_dict['sub']
            )

            # 4.) Associate the member with this organization
            organization = self.get_organization(
                self.request, self.kwargs.get('org_slug')
            )
            organization.members.add(new_user)
            ResourceRequest.objects.create(
                organization=self.organization,
                member=new_user,
                user=self.request.user,
                resource_class_path=RESOURCE_CHOICES[0][0],
                status=REQUEST_REQUESTED,
            )

            # 5.) Redirect the user to the next step in the Member-creation
            # process
            return HttpResponseRedirect(
                self.get_success_url(organization.slug, new_user.username)
            )

        else:
            # The request to create a user in VMI did not succeed. Show the errors
            # to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


class OrgCreateMemberBasicInfoView(LoginRequiredMixin, OrgCreateMemberMixin, FormView):
    """View to fill in basic info about a Member that was just created at an Organization."""

    template_name = 'org/member_basic_info.html'
    form_class = UpdateNewMemberAtOrgBasicInfoForm
    login_url = 'home'
    # If there are any non-form errors, they can be stored in self.errors, and
    # will be displayed in the template.
    errors = {}

    def get_success_url(self, org_slug, username):
        """A successful update redirects to the next step in the process."""
        return reverse(
            'org:org_create_member_verify_identity',
            kwargs={'org_slug': org_slug, 'username': username},
        )

    def form_valid(self, form):
        """
        If the form is valid, then update the user in VMI:
         1.) verify that the request.user has a UserSocialAuth object for VMI
         2.) verify that the Member has a UserSocialAuth object for VMI
         3.) make a request to VMI to update the new user
         4.) update a new Member with the response from VMI.
         5.) redirect the user to the next step in the Member-creation process
        """
        # 1.) Verify that the request.user has a UserSocialAuth object for VMI
        request_user_social_auth = self.request.user.social_auth.filter(
            provider='verifymyidentity-openidconnect'
        ).first()
        # If the request.user does not have a UserSocialAuth for VMI, then
        # return the error to the user.
        if not request_user_social_auth:
            self.errors = {
                'user': 'User has no association with {}'.format(
                    'verifymyidentity-openidconnect'
                )
            }
            return self.render_to_response(self.get_context_data())

        # 2.) Verify that the Member has a UserSocialAuth object for VMI
        member_social_auth = self.member.social_auth.filter(
            provider='verifymyidentity-openidconnect'
        ).first()
        # If the Member does not have a UserSocialAuth for VMI, return an error
        # to the user.
        if not member_social_auth:
            self.errors = {
                'member': 'Member has no association with {}'.format(
                    'verifymyidentity-openidconnect'
                )
            }
            return self.render_to_response(self.get_context_data())

        # 3.) Make a request to VMI to update the new user
        # The data to be PUT to VMI.
        # (at this point we know the form itself is valid; only put fields that are non-empty)
        data = {k: v for k, v in form.cleaned_data.items() if bool(v) is True}

        # PUT the data to VMI
        url = '{}/api/v1/user/{}/'.format(
            settings.SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_HOST, member_social_auth.uid
        )
        headers = {
            'Authorization': "Bearer {}".format(request_user_social_auth.access_token)
        }
        response = requests.put(url=url, data=data, headers=headers)

        if response.status_code in [401, 403]:
            refreshed = refresh_access_token(request_user_social_auth)
            if refreshed:  # repeat the previous request
                headers = {
                    'Authorization': "Bearer {}".format(
                        request_user_social_auth.access_token
                    )
                }
                response = requests.put(url=url, data=data, headers=headers)

        # 4.) Update a new Member with the response from VMI.
        # If the request successfully updated a user in VMI, then use that data
        # to update the Member in smh_app. If not, then show the error to the
        # user.
        if response.status_code == 200:
            response_data_dict = json.loads(response.content)
            # Update the Member
            self.member.email = response_data_dict['email']
            self.member.save()

            # Redirect the user to the next step in the Member-creation process
            return HttpResponseRedirect(
                self.get_success_url(
                    self.organization.slug, self.member.username)
            )
        else:
            # The request to update a user in VMI did not succeed, so show
            # errors to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


class OrgCreateMemberVerifyIdentityView(
    LoginRequiredMixin, OrgCreateMemberMixin, FormView
):
    """View to verify identity for a Member that was just created at an Organization."""

    template_name = 'org/member_verify_identity.html'
    form_class = VerifyMemberIdentityForm
    login_url = 'home'
    # If there are any non-form errors, they can be stored in self.errors, and
    # will be displayed in the template.
    errors = {}

    def get_success_url(self, org_slug, username):
        """A successful verification redirects to the next step in the process."""
        return reverse(
            # skip 'org:member_additional_info' for now
            'org:org_create_member_almost_done',
            kwargs={'org_slug': org_slug, 'username': username},
        )

    def form_valid(self, form):
        """
        If the form is valid, then update the user in VMI:
         1.) verify that the request.user has a UserSocialAuth object for VMI
         2.) verify that the Member has a UserSocialAuth object for VMI
         3.) make a request to VMI to get the user's identity assurance uuid
         4.) make a request to VMI to update the user's identity assurance
         5.) redirect the user to the next step in the Member-creation process
        """
        # Only post the form_data if it's non-empty -- otherwise, we can skip
        # this step
        form_data = {k: v for k, v in form.cleaned_data.items()
                     if bool(v) is True}
        if bool(form_data) is True:
            # 1.) Verify that the request.user has a UserSocialAuth object for
            # VMI
            request_user_social_auth = self.request.user.social_auth.filter(
                provider='verifymyidentity-openidconnect'
            ).first()
            # If the request.user does not have a UserSocialAuth for VMI, then
            # return the error to the user.
            if not request_user_social_auth:
                self.errors = {
                    'user': 'User has no association with {}'.format(
                        'verifymyidentity-openidconnect'
                    )
                }
                return self.render_to_response(self.get_context_data())

            # 2.) Verify that the Member has a UserSocialAuth object for VMI
            member_social_auth = self.member.social_auth.filter(
                provider='verifymyidentity-openidconnect'
            ).first()
            # If the Member does not have a UserSocialAuth for VMI, return an
            # error to the user.
            if not member_social_auth:
                self.errors = {
                    'member': 'Member has no association with {}'.format(
                        'verifymyidentity-openidconnect'
                    )
                }
                return self.render_to_response(self.get_context_data())

            headers = {
                'Authorization': "Bearer {}".format(
                    request_user_social_auth.access_token
                )
            }
            # 4.) Make a request to VMI to update the user's identity assurance
            url = '{}/api/v1/user/{}/id-assurance/'.format(
                settings.SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_HOST, member_social_auth.uid
            )

            data = {'subject_user': member_social_auth.uid, **form_data}

            # POST the data to the VMI endpoint for identity verification
            response = requests.post(url=url, json=data, headers=headers)

            if response.status_code in [401, 403]:
                refreshed = refresh_access_token(request_user_social_auth)
                if refreshed:  # repeat the previous request
                    headers = {
                        'Authorization': "Bearer {}".format(
                            request_user_social_auth.access_token
                        )
                    }
                    response = requests.post(
                        url=url, json=data, headers=headers)

            if response.status_code != 201:
                # The request to update a user in VMI did not succeed, so show
                # errors to the user.
                self.errors = json.loads(response.content)
                return self.render_to_response(self.get_context_data())

        # Redirect the user to the next step in the Member-creation process
        return HttpResponseRedirect(
            self.get_success_url(self.organization.slug, self.member.username)
        )


class OrgCreateMemberAdditionalInfoInfoView(
    LoginRequiredMixin, OrgCreateMemberMixin, FormView
):
    """View to fill in additional info about a Member that was just created at an Organization."""

    template_name = 'org/member_additional_info.html'
    form_class = UpdateNewMemberAtOrgAdditionalInfoForm
    login_url = 'home'
    # If there are any non-form errors, they can be stored in self.errors, and
    # will be displayed in the template.
    errors = {}

    def get_success_url(self, org_slug, username):
        """A successful verification redirects to the next step in the process."""
        return reverse(
            'org:org_create_member_almost_done',
            kwargs={'org_slug': org_slug, 'username': username},
        )

    def form_valid(self, form):
        """If form is valid, then redirect user to the next step in the Member-creation process."""
        # Redirect the user to the next step in the Member-creation process
        return HttpResponseRedirect(
            self.get_success_url(self.organization.slug, self.member.username)
        )


class OrgCreateMemberAlmostDoneView(LoginRequiredMixin, TemplateView):
    template_name = "org/member_almost_done.html"
    login_url = 'home'

    def get_organization(self, request, org_slug):
        """Get the Organization object that the org_slug refers to, or return a 404 response."""
        return get_object_or_404(
            Organization.objects.filter(agents=request.user), slug=org_slug
        )

    def get_member(self, organization, username):
        """Get the User object that the username refers to, or return a 404 response."""
        return get_object_or_404(
            get_user_model().objects.filter(member_organizations=organization),
            username=username,
        )

    def get_context_data(self, **kwargs):
        """Add the organization and member to the context."""
        organization = self.get_organization(
            self.request, self.kwargs.get('org_slug'))
        kwargs.setdefault('organization', organization)
        member = self.get_member(organization, self.kwargs.get('username'))
        kwargs.setdefault('member', member)

        # Create a uid and a token for the member, and use them to create a URL
        # for allowing the member to set their password.
        uid = urlsafe_base64_encode(force_bytes(member.pk)).decode('utf-8')
        token = token_generator.make_token(member)
        relative_url_to_set_password = reverse(
            'org:org_create_member_complete',
            kwargs={
                'org_slug': organization.slug,
                'username': member.username,
                'uidb64': uid,
                'token': token,
            },
        )
        full_url_to_set_password = self.request.build_absolute_uri(
            relative_url_to_set_password
        )
        kwargs.setdefault('url_to_set_password', full_url_to_set_password)
        kwargs.setdefault('qrcode', make_qr_code(full_url_to_set_password))

        return super().get_context_data(**kwargs)


class OrgCreateMemberCompleteView(OrgCreateMemberMixin, FormView):
    """View for the new Member to complete their account creation."""

    template_name = "org/member_complete.html"
    form_class = UpdateNewMemberAtOrgMemberForm
    login_url = 'home'
    # If there are any non-form errors, they can be stored in self.errors, and
    # will be displayed in the template.
    errors = {}

    def get_organization(self, request, org_slug):
        """
        Get the Organization object that the org_slug refers to, or return a 404 response.

        We override the OrgCreateMemberMixin method here, since the request.user
        is not required to be an Organization user (like an employee) at this
        Organization.
        """
        return get_object_or_404(Organization.objects.all(), slug=org_slug)

    def get_success_url(self, org_slug, username):
        """A successful verification redirects to home: goes to dashboard or prompts login."""
        return reverse('home')

    def token_is_valid(self, uidb64, token):
        """Return whether the token is valid (for the user)."""
        uid = urlsafe_base64_decode(uidb64).decode()
        user = self.member if self.member.pk == int(uid) else None
        return token_generator.check_token(user, token)

    def get(self, *args, **kwargs):
        """GETting the OrgCreateMemberCompleteView is only allowed with a valid token."""
        self.organization = self.get_organization(
            self.request, self.kwargs.get('org_slug')
        )
        self.member = self.get_member(
            self.organization, self.kwargs.get('username'))

        if self.token_is_valid(uidb64=kwargs['uidb64'], token=kwargs['token']):
            # The token is valid, so render the page to the user
            return self.render_to_response(self.get_context_data())
        else:
            # The token is not valid, so redirect user to the
            # org_create_member_invalid_token page
            redirect_url = reverse(
                'org:org_create_member_invalid_token',
                kwargs={'org_slug': kwargs['org_slug'],
                        'username': kwargs['username']},
            )
            return HttpResponseRedirect(redirect_url)

    def post(self, *args, **kwargs):
        """POSTing to the OrgCreateMemberCompleteView is only allowed with a valid token."""
        self.organization = self.get_organization(
            self.request, self.kwargs.get('org_slug')
        )
        self.member = self.get_member(
            self.organization, self.kwargs.get('username'))

        if self.token_is_valid(uidb64=kwargs['uidb64'], token=kwargs['token']):
            # The token is valid, so call the super().post() method
            return super().post(*args, **kwargs)
        else:
            # The token is not valid, so redirect user to the
            # org_create_member_invalid_token page
            redirect_url = reverse(
                'org:org_create_member_invalid_token',
                kwargs={'org_slug': kwargs['org_slug'],
                        'username': kwargs['username']},
            )
            return HttpResponseRedirect(redirect_url)

    def form_valid(self, form):
        """
        If form is valid, then create a ResourceGrant, set password, redirect user to the next step.

        If the form is valid, that means that the member is approving the Organization's
        ResourceRequest, and is also setting their password. Therefore, we
         1.) verify that the request.user (the Member) has a UserSocialAuth object for VMI
         2.) find and update the relevant ResourceRequest to be approved
         3.) create a ResourceGrant object
         4.) make a request to VMI to update the member's password in VMI
         5.) set the member's password locally
         6.) redirect the user to the next step in the Member-creation process
        """
        # 1.) Verify that the request.user has a UserSocialAuth object for VMI
        # request_user_id = urlsafe_base64_decode(self.kwargs.get('uidb64'))
        # request_user = Member.objects.get(pk=request_user_id)

        request_user_social_auth = self.member.social_auth.filter(
            provider='verifymyidentity-openidconnect'
        ).first()

        # If the request.user does not have a UserSocialAuth for VMI, then
        # return the error to the user.
        if not request_user_social_auth:
            self.errors = {
                'user': 'User has no association with {}'.format(
                    'verifymyidentity-openidconnect'
                )
            }
            return self.render_to_response(self.get_context_data())

        # 2.) Find and update the ResourceRequest for this Member to be
        # approved
        resource_request = ResourceRequest.objects.filter(
            member=self.member, organization=self.organization
        ).first()
        if resource_request is None:
            resource_request = ResourceRequest(
                member=self.member,
                organization=self.organization,
                user=self.request.user,
                resource_class_path=RESOURCE_CHOICES[0][0],
            )
        resource_request.status = REQUEST_APPROVED
        resource_request.save()

        # also ensure the association between the member and the organization
        if self.organization not in self.member.member_organizations.all():
            self.member.member_organizations.add(self.organization)

        # 3.) Create a ResourceGrant object for the ResourceRequest and the
        # Member
        ResourceGrant.objects.get_or_create(
            organization=resource_request.organization,
            member=resource_request.member,
            resource_class_path=resource_request.resource_class_path,
            resource_request=resource_request,
        )

        # 4.) Make a request to VMI to update the member's password in VMI
        org_user_social_auth = resource_request.user.social_auth.filter(
            provider='verifymyidentity-openidconnect'
        ).first()
        data = {'password': form.data['password1']}
        url = '{}/api/v1/user/{}/'.format(
            settings.SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_HOST, request_user_social_auth.uid
        )
        headers = {
            'Authorization': "Bearer {}".format(org_user_social_auth.access_token)
        }
        response = requests.put(url=url, data=data, headers=headers)

        if response.status_code in [401, 403]:
            refreshed = refresh_access_token(org_user_social_auth)
            if refreshed:  # repeat the previous request
                headers = {
                    'Authorization': "Bearer {}".format(
                        org_user_social_auth.access_token
                    )
                }
                response = requests.put(url=url, data=data, headers=headers)

        if response.status_code == 200:
            response_data_dict = json.loads(response.content)
            # Update the Member. Note: we set the password locally, in order to
            # invalidate the member's token (the one in kwargs['token']).
            self.member.email = response_data_dict['email']
            self.member.profile.picture_url = response_data_dict.get('picture')
            self.member.set_password(form.data['password1'])
            self.member.save()

            # 6.) Redirect the user to authenticate in VMI, and to accept this
            # application's access (and get an access token as a result).
            url_vmi_auth = reverse('social:begin', args=(
                'verifymyidentity-openidconnect',))
            url_success = self.get_success_url(
                self.organization.slug, self.member.username
            )
            return HttpResponseRedirect('{}?next={}'.format(url_vmi_auth, url_success))
        else:
            # The request to update a user in VMI did not succeed, so show
            # errors to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


class OrgCreateMemberInvalidTokenView(OrgCreateMemberMixin, TemplateView):
    template_name = "org/member_complete_invalid_token.html"
    login_url = 'home'
    errors = {}

    def get_organization(self, request, org_slug):
        """
        Get the Organization object that the org_slug refers to, or return a 404 response.

        We override the OrgCreateMemberMixin method here, since the request.user
        is not required to be an Organization user (like an employee) at this
        Organization.
        """
        return get_object_or_404(Organization.objects.all(), slug=org_slug)

    def post(self, request, *args, **kwargs):
        from django.http import HttpResponseNotAllowed

        return HttpResponseNotAllowed('GET')


class OrgCreateMemberSuccessView(OrgCreateMemberMixin, TemplateView):
    template_name = "org/member_success.html"
    login_url = 'home'
    errors = {}

    def get_organization(self, request, org_slug):
        """
        Get the Organization object that the org_slug refers to, or return a 404 response.

        We override the OrgCreateMemberMixin method here, since the request.user
        is not required to be an Organization user (like an employee) at this
        Organization.
        """
        return get_object_or_404(Organization.objects.all(), slug=org_slug)

    def post(self, request, *args, **kwargs):
        from django.http import HttpResponseNotAllowed

        return HttpResponseNotAllowed('GET')


class SearchMembersAPI(LoginRequiredMixin, View):
    ''' Setting up a local endpoint for users here. '''

    def get(self, request, *args, **kwargs):
        # Get User objects that are not Organization agents,
        # along with related UserProfile objects,
        # and return a list of data objects, one per member
        users = get_user_model().objects.filter(agent_organizations__isnull=True)
        data = [
            {
                'user': {
                    key: val
                    for key, val in user.__dict__.items()
                    if key not in ['password'] and key[0] != '_' and key[:3] != 'is_'
                },
                'profile': user.profile.as_dict(),
            }
            for user in users
        ]
        return JsonResponse(data, safe=False)


class SearchView(LoginRequiredMixin, TemplateView):
    """template view that mostly uses javascript to render content"""

    template_name = "org/search.html"
