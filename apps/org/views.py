import json
import requests
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, reverse
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic.base import TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views import View

from social_django.models import UserSocialAuth

from .tokens import default_token_generator
from .forms import (
    CreateNewMemberAtOrgForm, UpdateNewMemberAtOrgBasicInfoForm,
    UpdateNewMemberAtOrgAdditionalInfoForm, UpdateNewMemberAtOrgMemberForm,
    VerifyMemberIdentityForm
)
from .models import (
    Organization, REQUEST_APPROVED, REQUEST_REQUESTED, RESOURCE_CHOICES,
    ResourceGrant, ResourceRequest
)
from apps.member.models import Member


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "org/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add the user's Organizations, to the context."""
        # All of the Organizations that the request.user is a part of
        organizations = self.request.user.organization_set.all()

        kwargs.setdefault('organizations', organizations)

        return super().get_context_data(**kwargs)


class CreateOrganizationView(LoginRequiredMixin, CreateView):
    model = Organization
    fields = ['name', 'users']
    template_name = 'org/organization.html'
    success_url = reverse_lazy('org:dashboard')

    def form_valid(self, form):
        """Override this method to also associate the creator with the new Organization."""
        # Now that the form has passed validation, save the object, then add
        # the request.user to its users.
        response = super().form_valid(form)
        form.instance.users.add(self.request.user)
        return response


class UpdateOrganizationView(LoginRequiredMixin, UpdateView):
    model = Organization
    fields = ['name', 'users']
    template_name = 'org/organization.html'
    success_url = reverse_lazy('org:dashboard')

    def get_queryset(self):
        """A user may only edit Organizations that they are associated with."""
        qs = super().get_queryset()
        return qs.filter(users=self.request.user)


class DeleteOrganizationView(LoginRequiredMixin, DeleteView):
    model = Organization
    success_url = reverse_lazy('organization-list')
    template_name = 'org/organization_confirm_delete.html'
    success_url = reverse_lazy('org:dashboard')

    def get_queryset(self):
        """A user may only delete Organizations that they are associated with."""
        qs = super().get_queryset()
        return qs.filter(users=self.request.user)


class JoinOrganizationView(LoginRequiredMixin, BaseDetailView):
    model = Organization
    success_url = reverse_lazy('org:dashboard')
    token_kwarg = "token"
    token_generator = default_token_generator

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return str(self.success_url)  # success_url may be lazy

    def render_to_response(self, context):
        tkn = self.kwargs.get(self.token_kwarg)
        if self.token_generator.check_token(self.object, tkn):
            self.object.users.add(self.request.user)
            return HttpResponseRedirect(self.get_success_url())
        raise Http404()


class OrgCreateMemberMixin:
    """A mixin for the create member views."""
    def get_organization(self, request, org_slug):
        """Get the Organization object that the org_slug refers to, or return a 404 response."""
        return get_object_or_404(
            Organization.objects.filter(users=request.user),
            slug=org_slug
        )

    def get_member(self, organization, username):
        """Get the Member object that the username refers to, or return a 404 response."""
        user = get_object_or_404(
            get_user_model().objects.filter(member__organizations=organization),
            username=username
        )
        return user.member

    def get_context_data(self, **kwargs):
        """Get the context data for the template."""
        kwargs.setdefault('organization', self.organization)
        kwargs.setdefault('member', self.member)
        kwargs.setdefault('errors', self.errors)
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        """Set the self.organization and self.member."""
        self.organization = self.get_organization(request, self.kwargs.get('org_slug'))
        self.member = self.get_member(self.organization, self.kwargs.get('username'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Set the self.organization and self.member."""
        self.organization = self.get_organization(request, self.kwargs.get('org_slug'))
        self.member = self.get_member(self.organization, self.kwargs.get('username'))
        return super().post(request, *args, **kwargs)


class OrgCreateMemberView(LoginRequiredMixin, OrgCreateMemberMixin, FormView):
    """A view for allowing a User at an Organization to create a Member for that Organization."""
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
            kwargs={'org_slug': org_slug, 'username': username}
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
         4.) create a ResourceRequest for the new Member's data from the relavant Organization
         5.) redirect the user to the next step in the Member-creation process
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

        # 2.) Make a request to VMI to create the new user
        # The data to be POSTed to VMI
        data = {
            'given_name': self.request.POST.get('first_name'),
            'family_name': self.request.POST.get('last_name'),
            'preferred_username': self.request.POST.get('username'),
            'phone_number': self.request.POST.get('phone_number', '').strip() or 'none',
            # The following fields are required by VMI, but we don't have values
            # for them yet, so we make up some data now, and require the user
            # to fill them in during the next steps of the Member creation process.
            'gender': '',
            'password': 'abcde12345',
            'birthdate': '2000-01-01',
            'nickname': self.request.POST.get('first_name'),
            'email': '{}_{}_{}@example.com'.format(
                "".join(re.findall("[a-zA-Z]+", self.request.POST.get('username'))),
                "".join(re.findall("[a-zA-Z]+", self.request.POST.get('first_name'))),
                "".join(re.findall("[a-zA-Z]+", self.request.POST.get('last_name'))),
            ),
        }
        # POST the data to VMI
        response = requests.post(
            url=settings.SOCIAL_AUTH_VMI_HOST + '/api/v1/user/',
            data=data,
            headers={'Authorization': "Bearer {}".format(request_user_social_auth.access_token)}
        )

        # 3.) Create a new Member with the response from VMI.
        # If the request successfully created a user in VMI, then use that data
        # to create a Member that is linked to the VMI user through a UserSocialAuth.
        if response.status_code == 201:
            response_data_dict = json.loads(response.content)
            # Create the Member, and associate with this Organization
            new_user = get_user_model().objects.create(
                first_name=response_data_dict['given_name'],
                last_name=response_data_dict['family_name'],
                username=response_data_dict['preferred_username'],
            )
            new_member = new_user.member
            organization = self.get_organization(self.request, self.kwargs.get('org_slug'))
            new_member.organizations.add(organization)
            # Save the member's picture URL
            new_user.userprofile.picture_url = response_data_dict['picture']
            new_user.userprofile.save()
            # Create a UserSocialAuth for the new Member
            UserSocialAuth.objects.create(
                user_id=new_user.id,
                provider='vmi',
                uid=response_data_dict['sub']
            )

            # 4.) create a ResourceRequest for the new Member's data from the relavant Organization
            ResourceRequest.objects.create(
                organization=self.organization,
                member=new_user,
                user=self.request.user,
                resource_class_path=RESOURCE_CHOICES[0][0],
                status=REQUEST_REQUESTED
            )

            # 5.) Redirect the user to the next step in the Member-creation process
            return HttpResponseRedirect(self.get_success_url(organization.slug, new_user.username))
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
            kwargs={'org_slug': org_slug, 'username': username}
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
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the request.user does not have a UserSocialAuth for VMI, then
        # return the error to the user.
        if not request_user_social_auth:
            self.errors = {
                'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)
            }
            return self.render_to_response(self.get_context_data())

        # 2.) Verify that the Member has a UserSocialAuth object for VMI
        member_social_auth = self.member.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the Member does not have a UserSocialAuth for VMI, return an error to the user.
        if not member_social_auth:
            self.errors = {
                'member': 'Member has no association with {}'.format(settings.SOCIAL_AUTH_NAME)
            }
            return self.render_to_response(self.get_context_data())

        # 3.) Make a request to VMI to update the new user
        # The data to be PUT to VMI
        data = {
            'gender': self.request.POST.get('gender'),
            'birthdate': self.request.POST.get('birthdate'),
            'nickname': self.request.POST.get('nickname'),
            'email': self.request.POST.get('email'),
        }
        # PUT the data to VMI
        url = '{}/api/v1/user/{}/'.format(settings.SOCIAL_AUTH_VMI_HOST, member_social_auth.uid)
        headers = {'Authorization': "Bearer {}".format(request_user_social_auth.access_token)}
        response = requests.put(url=url, data=data, headers=headers)

        # 4.) Update a new Member with the response from VMI.
        # If the request successfully updated a user in VMI, then use that data
        # to update the Member in smh_app. If not, then show the error to the user.
        if response.status_code == 200:
            response_data_dict = json.loads(response.content)
            # Update the Member
            self.member.user.email = response_data_dict['email']
            self.member.user.userprofile.picture_url = response_data_dict['picture']
            self.member.user.save()

            # Redirect the user to the next step in the Member-creation process
            return HttpResponseRedirect(
                self.get_success_url(self.organization.slug, self.member.user.username)
            )
        else:
            # The request to update a user in VMI did not succeed, so show errors to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


class OrgCreateMemberVerifyIdentityView(LoginRequiredMixin, OrgCreateMemberMixin, FormView):
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
            'org:org_create_member_additional_info',
            kwargs={'org_slug': org_slug, 'username': username}
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

        # 2.) Verify that the Member has a UserSocialAuth object for VMI
        member_social_auth = self.member.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the Member does not have a UserSocialAuth for VMI, return an error to the user.
        if not member_social_auth:
            self.errors = {
                'member': 'Member has no association with {}'.format(settings.SOCIAL_AUTH_NAME)
            }
            return self.render_to_response(self.get_context_data())

        headers = {'Authorization': "Bearer {}".format(request_user_social_auth.access_token)}
        # 4.) Make a request to VMI to update the user's identity assurance
        url = '{}/api/v1/user/{}/id-assurance/'.format(
            settings.SOCIAL_AUTH_VMI_HOST,
            member_social_auth.uid,
        )
        data = {
            'subject_user': member_social_auth.uid,
            'classification': self.request.POST.get('classification'),
            'description': self.request.POST.get('description'),
            'exp': self.request.POST.get('expiration_date'),
        }
        # POST the data to the VMI endpoint for identity verification
        response = requests.post(url=url, json=data, headers=headers)

        if response.status_code == 201:
            # Redirect the user to the next step in the Member-creation process
            return HttpResponseRedirect(
                self.get_success_url(self.organization.slug, self.member.user.username)
            )
        else:
            # The request to update a user in VMI did not succeed, so show errors to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


class OrgCreateMemberAdditionalInfoInfoView(LoginRequiredMixin, OrgCreateMemberMixin, FormView):
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
            kwargs={'org_slug': org_slug, 'username': username}
        )

    def form_valid(self, form):
        """If form is valid, then redirect user to the next step in the Member-creation process."""
        # Redirect the user to the next step in the Member-creation process
        return HttpResponseRedirect(
            self.get_success_url(self.organization.slug, self.member.user.username)
        )


class OrgCreateMemberAlmostDoneView(LoginRequiredMixin, TemplateView):
    template_name = "org/member_almost_done.html"
    login_url = 'home'

    def get_organization(self, request, org_slug):
        """Get the Organization object that the org_slug refers to, or return a 404 response."""
        return get_object_or_404(
            Organization.objects.filter(users=request.user),
            slug=org_slug
        )

    def get_member(self, organization, username):
        """Get the Member object that the username refers to, or return a 404 response."""
        user = get_object_or_404(
            get_user_model().objects.filter(member__organizations=organization),
            username=username
        )
        return user.member

    def get_context_data(self, **kwargs):
        """Add the Organization and Member to the context."""
        organization = self.get_organization(self.request, self.kwargs.get('org_slug'))
        kwargs.setdefault('organization', organization)
        member = self.get_member(organization, self.kwargs.get('username'))
        kwargs.setdefault('member', member)

        # Create a uid and a token for the member, and use them to create a URL
        # for allowing the member to set their password.
        uid = urlsafe_base64_encode(force_bytes(member.pk)).decode('utf-8')
        token = token_generator.make_token(member.user)
        relative_url_to_set_password = reverse(
            'org:org_create_member_complete',
            kwargs={
                'org_slug': organization.slug,
                'username': member.user.username,
                'uidb64': uid,
                'token': token
            }
        )
        full_url_to_set_password = self.request.build_absolute_uri(relative_url_to_set_password)
        kwargs.setdefault('url_to_set_password', full_url_to_set_password)

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
        return get_object_or_404(
            Organization.objects.all(),
            slug=org_slug
        )

    def get_success_url(self, org_slug, username):
        """A successful verification redirects to the next step in the process."""
        return reverse(
            'org:org_create_member_success',
            kwargs={'org_slug': org_slug, 'username': username}
        )

    def token_is_valid(self, uidb64, token):
        """Return whether the token is valid (for the user)."""
        uid = urlsafe_base64_decode(uidb64).decode()
        user = self.member.user if self.member.pk == int(uid) else None
        return token_generator.check_token(user, token)

    def get(self, *args, **kwargs):
        """GETting the OrgCreateMemberCompleteView is only allowed with a valid token."""
        self.organization = self.get_organization(self.request, self.kwargs.get('org_slug'))
        self.member = self.get_member(self.organization, self.kwargs.get('username'))

        if self.token_is_valid(uidb64=kwargs['uidb64'], token=kwargs['token']):
            # The token is valid, so render the page to the user
            return self.render_to_response(self.get_context_data())
        else:
            # The token is not valid, so redirect user to the org_create_member_invalid_token page
            redirect_url = reverse(
                'org:org_create_member_invalid_token',
                kwargs={'org_slug': kwargs['org_slug'], 'username': kwargs['username']}

            )
            return HttpResponseRedirect(redirect_url)

    def post(self, *args, **kwargs):
        """POSTing to the OrgCreateMemberCompleteView is only allowed with a valid token."""
        self.organization = self.get_organization(self.request, self.kwargs.get('org_slug'))
        self.member = self.get_member(self.organization, self.kwargs.get('username'))

        if self.token_is_valid(uidb64=kwargs['uidb64'], token=kwargs['token']):
            # The token is valid, so call the super().post() method
            return super().post(*args, **kwargs)
        else:
            # The token is not valid, so redirect user to the org_create_member_invalid_token page
            redirect_url = reverse(
                'org:org_create_member_invalid_token',
                kwargs={'org_slug': kwargs['org_slug'], 'username': kwargs['username']}

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

        request_user_social_auth = self.member.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()

        # If the request.user does not have a UserSocialAuth for VMI, then
        # return the error to the user.
        if not request_user_social_auth:
            self.errors = {
                'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)
            }
            return self.render_to_response(self.get_context_data())

        # 2.) Find and update the ResourceRequest for this Member to be approved
        resource_request = ResourceRequest.objects.filter(
            member=self.member.user,
            organization=self.organization,
        ).first()
        resource_request.status = REQUEST_APPROVED
        resource_request.save()

        # 3.) Create a ResourceGrant object for the ResourceRequest and the Member
        ResourceGrant.objects.get_or_create(
            organization=resource_request.organization,
            member=resource_request.member,
            resource_class_path=resource_request.resource_class_path,
            resource_request=resource_request
        )

        # 4.) Make a request to VMI to update the member's password in VMI
        org_user_social_auth = resource_request.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        data = {'password': form.data['password1']}
        url = '{}/api/v1/user/{}/'.format(settings.SOCIAL_AUTH_VMI_HOST, request_user_social_auth.uid)
        headers = {'Authorization': "Bearer {}".format(org_user_social_auth.access_token)}
        response = requests.put(url=url, data=data, headers=headers)

        if response.status_code == 200:
            response_data_dict = json.loads(response.content)
            # Update the Member. Note: we set the password locally, in order to
            # invalidate the member's token (the one in kwargs['token']).
            self.member.user.email = response_data_dict['email']
            self.member.user.userprofile.picture_url = response_data_dict['picture']
            self.member.user.set_password(form.data['password1'])
            self.member.user.save()

            # 6.) Redirect the user to authenticate in VMI, and to accept this
            # application's access (and get an access token as a result).
            url_vmi_auth = reverse('social:begin', args=(settings.SOCIAL_AUTH_NAME,))
            url_success = self.get_success_url(self.organization.slug, self.member.user.username)
            return HttpResponseRedirect('{}?next={}'.format(url_vmi_auth, url_success))
        else:
            # The request to update a user in VMI did not succeed, so show errors to the user.
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
        return get_object_or_404(
            Organization.objects.all(),
            slug=org_slug
        )

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
        return get_object_or_404(
            Organization.objects.all(),
            slug=org_slug
        )

    def post(self, request, *args, **kwargs):
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed('GET')


class LocalUserAPI(LoginRequiredMixin, View):
    ''' Setting up a local endpoint for users here. '''
    def get(self, request, *args, **kwargs):
        # picking the first organization here
        members = Member.objects.all()
        members_data = list(members.values())

        user_id_list = [mem.user.id for mem in members]

        users = get_user_model().objects.filter(pk__in=user_id_list)
        user_data = {user['id']: user for user in list(users.values())}

        # TODO: Save all the extra_data from vmi when we create member and link to VMI, including `picture`

        social_auth_data = list(get_user_model().social_auth.rel.related_model.objects.filter(user__pk__in=user_id_list).values())
        extra_data = {user['user_id']: user['extra_data'] for user in social_auth_data}

        for member in members_data:
            member['user'] = user_data.get(member['user_id'], {})
            member['extra_data'] = extra_data.get(member['user_id'], {})

        return JsonResponse(members_data, safe=False)


class SearchView(LoginRequiredMixin, TemplateView):
    """template view that mostly uses javascript to render content"""
    template_name = "org/search.html"
