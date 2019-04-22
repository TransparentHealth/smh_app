import json
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

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


@login_required(login_url='home')
def org_create_member_view(request, org_slug):
    """A view for allowing a User at an Organization to create a Member for that Organization."""
    organization = get_object_or_404(
        Organization.objects.filter(users=request.user),
        slug=org_slug
    )

    # If the user is GETting the page, then render the template.
    if request.method == 'GET':
        context = {'organization': organization, 'form': CreateNewMemberAtOrgForm()}
        return render(request, 'org/org_create_member.html', context=context)
    else:
        # The user is POSTing to create a new Member at the organization, so we:
        #   1.) validate the input
        #   2.) make a request to VMI to create the new user
        #   3.) create a new Member with the response from VMI

        # 1.) Validate the input. If the form is not valid, then return the errors
        # to the user.
        form = CreateNewMemberAtOrgForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                'org/org_create_member.html',
                context={'organization': organization, 'form': form}
            )

        # 2.) Make a request to VMI to create the new user
        request_user_social_auth = request.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the request.user does not have a UserSocialAuth for VMI, then
        # return the error to the user.
        if not request_user_social_auth:
            errors = {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            return render(
                request,
                'org/org_create_member.html',
                context={'organization': organization, 'form': form, 'errors': errors}
            )
        # The data to be POSTed to VMI
        data = {
            'given_name': request.POST.get('first_name'),
            'family_name': request.POST.get('last_name'),
            'preferred_username': request.POST.get('username'),
            'phone_number': request.POST.get('phone_number', '').strip() or 'none',
            # The following fields are required by VMI, but we don't have values
            # for them yet, so we make up some data now, and require the user
            # to fill them in during the next steps of the Member creation process.
            'gender': '',
            'password': 'abcde12345',
            'birthdate': '2000-01-01',
            'nickname': request.POST.get('first_name'),
            'email': 'test_{}_{}@example.com'.format(
                request.POST.get('first_name'),
                request.POST.get('last_name'),
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
            new_member.organizations.add(organization)
            # Create a UserSocialAuth for the new Member
            UserSocialAuth.objects.create(
                user_id=new_user.id,
                provider='vmi',
                uid=response_data_dict['sub']
            )
            # Redirect the user to the next step for creating a new Member
            return redirect(
                reverse(
                    'org:org_create_member_basic_info',
                    kwargs={'org_slug': org_slug, 'username': new_user.username}
                )
            )
        else:
            # The request to create a user in VMI did not succeed. Show the errors
            # to the user.
            errors = json.loads(response.content)
            return render(
                request,
                'org/org_create_member.html',
                context={'organization': organization, 'form': form, 'errors': errors}
            )


@login_required(login_url='home')
def org_create_member_basic_info_view(request, org_slug, username):
    """View to fill in basic info about a Member that was just created at an Organization."""
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

    # If the user is GETting the page, then render the template.
    if request.method == 'GET':
        context['form'] = UpdateNewMemberAtOrgBasicInfoForm()
        return render(request, 'org/member_basic_info.html', context=context)
    else:
        # The user is POSTing to update a Member at the organization, so we:
        #   1.) validate the input
        #   2.) make a request to VMI to update the user
        #   3.) update the Member with the response from VMI

        # 1.) Validate the input. If the form is not valid, then return the errors
        # to the user.
        form = UpdateNewMemberAtOrgBasicInfoForm(request.POST)
        if not form.is_valid():
            context['form'] = form
            return render(request, 'org/member_basic_info.html', context=context)

        # 2.) Make a request to VMI to update the new user
        request_user_social_auth = request.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the request.user does not have a UserSocialAuth for VMI, return an error to the user.
        if not request_user_social_auth:
            errors = {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            context['form'] = form
            context['errors'] = errors
            return render(request, 'org/member_basic_info.html', context=context)
        # The data to be PUT to VMI
        data = {
            'gender': request.POST.get('gender'),
            'birthdate': request.POST.get('birthdate'),
            'nickname': request.POST.get('nickname'),
            'email': request.POST.get('email'),
        }
        # Get the Member's UserSocialAuth object
        member_social_auth = member.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the Member does not have a UserSocialAuth for VMI, return an error to the user.
        if not member_social_auth:
            errors = {'member': 'Member has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            context['form'] = form
            context['errors'] = errors
            return render(request, 'org/member_basic_info.html', context=context)
        # PUT the data to VMI
        url = '{}/api/v1/user/{}/'.format(settings.SOCIAL_AUTH_VMI_HOST, member_social_auth.uid)
        headers = {'Authorization': "Bearer {}".format(request_user_social_auth.access_token)}
        response = requests.put(url=url, data=data, headers=headers)

        # 3.) Update a new Member with the response from VMI.
        # If the request successfully updated a user in VMI, then use that data
        # to update the Member in smh_app. If not, then show the error to the user.
        if response.status_code == 200:
            response_data_dict = json.loads(response.content)
            # Update the Member
            member.user.email = response_data_dict['email']
            member.user.save()
            # Redirect the user to the next step for creating a new Member
            return redirect(
                reverse(
                    'org:org_create_member_verify_identity',
                    kwargs={'org_slug': org_slug, 'username': user.username}
                )
            )
        else:
            # The request to update a user in VMI did not succeed, so show errors to the user.
            errors = json.loads(response.content)
            context['errors'] = errors
            return render(request, 'org/member_basic_info.html', context=context)


@login_required(login_url='home')
def org_create_member_verify_identity_view(request, org_slug, username):
    """View to verify identity for a Member that was just created at an Organization."""
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

    # If the user is GETting the page, then render the template.
    if request.method == 'GET':
        context['form'] = VerifyMemberIdentityForm()
        return render(request, 'org/member_verify_identity.html', context=context)
    else:
        # The user is POSTing to update a Member at the organization, so we:
        #   1.) validate the input
        #   2.) make a request to VMI to get the user's identity assurance uuid
        #   3.) make a request to VMI to update the user's identity assurance

        # 1.) Validate the input. If form is not valid, then return the errors to the user.
        form = VerifyMemberIdentityForm(request.POST)
        if not form.is_valid():
            context['form'] = form
            return render(request, 'org/member_verify_identity.html', context=context)

        # 2.) Make a request to VMI to get the user's identity assurance uuid
        request_user_social_auth = request.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the request.user does not have a UserSocialAuth for VMI, return an error to the user.
        if not request_user_social_auth:
            errors = {'user': 'User has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            context['form'] = form
            context['errors'] = errors
            return render(request, 'org/member_verify_identity.html', context=context)
        # Get the Member's UserSocialAuth object
        member_social_auth = member.user.social_auth.filter(
            provider=settings.SOCIAL_AUTH_NAME
        ).first()
        # If the Member does not have a UserSocialAuth for VMI, return an error to the user.
        if not member_social_auth:
            errors = {'member': 'Member has no association with {}'.format(settings.SOCIAL_AUTH_NAME)}
            context['form'] = form
            context['errors'] = errors
            return render(request, 'org/member_verify_identity.html', context=context)
        # Get the member's identity assurance uuid
        url = '{}/api/v1/user/{}/id-assurance/'.format(
            settings.SOCIAL_AUTH_VMI_HOST,
            member_social_auth.uid,
        )
        headers = {'Authorization': "Bearer {}".format(request_user_social_auth.access_token)}
        response = requests.get(url=url, headers=headers)
        # If the request to get the Member's identity assurance uuid from VMI fails,
        # display the error to the user.
        if response.status_code != 200:
            context['errors'] = json.loads(response.content)
            return render(request, 'org/member_verify_identity.html', context=context)
        else:
            identity_assurance_uuid = json.loads(response.content)[0].get('uuid')

        # 3.) Make a request to VMI to update the user's identity assurance
        url = '{}/api/v1/user/{}/id-assurance/{}/'.format(
            settings.SOCIAL_AUTH_VMI_HOST,
            member_social_auth.uid,
            identity_assurance_uuid
        )
        data = {
            'subject_user': member_social_auth.uid,
            'classification': request.POST.get('classification'),
            'description': request.POST.get('description'),
            'exp': request.POST.get('expiration_date'),
        }
        # PUT the data to the VMI endpoint for identity verification
        response = requests.put(url=url, data=data, headers=headers)

        if response.status_code == 200:
            # Redirect the user to the next step for creating a new Member
            return redirect(
                reverse(
                    'org:org_create_member_additional_info',
                    kwargs={'org_slug': org_slug, 'username': user.username}
                )
            )
        else:
            # The request to update a user in VMI did not succeed, so show errors to the user.
            errors = json.loads(response.content)
            context['errors'] = errors
            return render(request, 'org/member_verify_identity.html', context=context)


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
