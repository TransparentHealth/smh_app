import json
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from social_django.models import UserSocialAuth

from .forms import (
    CreateNewMemberAtOrgForm, UpdateNewMemberAtOrgBasicInfoForm, VerifyMemberIdentityForm
)
from .models import Organization


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


class OrgCreateMemberView(LoginRequiredMixin, FormView):
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

    def get_organization(self, request, org_slug):
        """Get the Organization object that the org_slug refers to, or return a 404 response."""
        return get_object_or_404(
            Organization.objects.filter(users=request.user),
            slug=org_slug
        )

    def get_context_data(self, **kwargs):
        """Get the context data for the template."""
        kwargs.setdefault(
            'organization',
            self.get_organization(self.request, self.kwargs.get('org_slug'))
        )
        kwargs.setdefault('errors', self.errors)
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        """
        If the form is valid, then create the new member:
         1.) Verify that the request.user has a UserSocialAuth object for VMI
         2.) make a request to VMI to create the new user in VMI
         3.) create a new Member with the response from VMI
         4.) redirect the user to the next step in the Member-creation process
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
            'email': 'test_{}_{}@example.com'.format(
                self.request.POST.get('first_name'),
                self.request.POST.get('last_name'),
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
            # Create a UserSocialAuth for the new Member
            UserSocialAuth.objects.create(
                user_id=new_user.id,
                provider='vmi',
                uid=response_data_dict['sub']
            )

            # 4.) Redirect the user to the next step in the Member-creation process
            return HttpResponseRedirect(self.get_success_url(organization.slug, new_user.username))
        else:
            # The request to create a user in VMI did not succeed. Show the errors
            # to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


class OrgCreateMemberBasicInfoView(LoginRequiredMixin, FormView):
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
            self.member.user.save()

            # Redirect the user to the next step in the Member-creation process
            return HttpResponseRedirect(
                self.get_success_url(self.organization.slug, self.member.user.username)
            )
        else:
            # The request to update a user in VMI did not succeed, so show errors to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


class OrgCreateMemberVerifyIdentityView(LoginRequiredMixin, FormView):
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

        # 3.) Make a request to VMI to get the user's identity assurance uuid
        url = '{}/api/v1/user/{}/id-assurance/'.format(
            settings.SOCIAL_AUTH_VMI_HOST,
            member_social_auth.uid,
        )
        headers = {'Authorization': "Bearer {}".format(request_user_social_auth.access_token)}
        response = requests.get(url=url, headers=headers)
        # If the request to get the Member's identity assurance uuid from VMI fails,
        # display the error to the user.
        if response.status_code != 200:
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())
        else:
            identity_assurance_uuid = json.loads(response.content)[0].get('uuid')

        # 4.) Make a request to VMI to update the user's identity assurance
        url = '{}/api/v1/user/{}/id-assurance/{}/'.format(
            settings.SOCIAL_AUTH_VMI_HOST,
            member_social_auth.uid,
            identity_assurance_uuid
        )
        data = {
            'subject_user': member_social_auth.uid,
            'classification': self.request.POST.get('classification'),
            'description': self.request.POST.get('description'),
            'exp': self.request.POST.get('expiration_date'),
        }
        # PUT the data to the VMI endpoint for identity verification
        response = requests.put(url=url, data=data, headers=headers)

        if response.status_code == 200:
            # Redirect the user to the next step in the Member-creation process
            return HttpResponseRedirect(
                self.get_success_url(self.organization.slug, self.member.user.username)
            )
        else:
            # The request to update a user in VMI did not succeed, so show errors to the user.
            self.errors = json.loads(response.content)
            return self.render_to_response(self.get_context_data())


@login_required(login_url='home')
def org_create_member_additional_info_view(request, org_slug, username):
    """View to fill in additional info about a Member that was just created at an Organization."""
    organization = get_object_or_404(
        Organization.objects.filter(users=request.user),
        slug=org_slug
    )
    user = get_object_or_404(
        get_user_model().objects.filter(member__organizations=organization),
        username=username
    )
    member = user.member

    # The context to be used in the template
    context = {'organization': organization, 'member': member}

    return render(request, 'org/member_additional_info.html', context=context)


@login_required(login_url='home')
def org_create_member_almost_done_view(request, org_slug, username):
    """View to open a page for the new Member to complete account creation at an Organization."""
    organization = get_object_or_404(
        Organization.objects.filter(users=request.user),
        slug=org_slug
    )
    user = get_object_or_404(
        get_user_model().objects.filter(member__organizations=organization),
        username=username
    )
    member = user.member

    return render(
        request,
        'org/member_almost_done.html',
        context={'organization': organization, 'member': member}
    )


@login_required(login_url='home')
def org_create_member_complete_view(request, org_slug, username):
    """View to allow the new Member to complete account creation at an Organization."""
    organization = get_object_or_404(
        Organization.objects.filter(users=request.user),
        slug=org_slug
    )
    user = get_object_or_404(
        get_user_model().objects.filter(member__organizations=organization),
        username=username
    )
    member = user.member

    return render(
        request,
        'org/member_complete.html',
        context={'organization': organization, 'member': member}
    )
