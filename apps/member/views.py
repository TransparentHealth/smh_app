import requests

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from jwkest.jwt import JWT
from .constants import RECORDS
from .models import Member
from .utils import get_member_data
from apps.org.models import (
    ResourceGrant, ResourceRequest, REQUEST_APPROVED, REQUEST_DENIED
)


def get_id_token_payload(user):
    # Get the ID Token and parse it.
    try:
        vmi = user.social_auth.filter(provider='vmi')[0]
        extra_data = vmi.extra_data
        if 'id_token' in vmi.extra_data.keys():
            id_token = extra_data.get('id_token')
            parsed_id_token = JWT().unpack(id_token)
            parsed_id_token = parsed_id_token.payload()
        else:
            parsed_id_token = {'sub': '', 'ial': '1'}

    except Exception:
        parsed_id_token = {'sub': '', 'ial': '1'}

    return parsed_id_token


def get_fake_context_data(context):
    # just-for-show data from fake endpoint, unrelated to any user/member/org.
    url_base = 'http://fhir-test.sharemy.health:8080/fhir/baseDstu3/'

    patient_id = '304'

    patient_url = url_base + 'Patient/' + patient_id
    patient_response = requests.get(url=patient_url)
    patient_data = patient_response.json()

    organization_url = url_base + \
        patient_data['generalPractitioner'][0]['reference']
    organization_response = requests.get(url=organization_url)
    organization_data = organization_response.json()

    medication_request_url = url_base + 'MedicationRequest?patient=' + patient_id
    medication_request_response = requests.get(url=medication_request_url)
    medication_request_data = medication_request_response.json()

    context['patient_data'] = patient_data
    context['organization_data'] = organization_data
    context['medication_request_data'] = medication_request_data
    context['records_options'] = RECORDS

    return context


class RecordsView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "records.html"
    default_resource_name = 'sharemyhealth'
    default_record_type = 'Condition'

    def get_context_data(self, **kwargs):
        """Add records data into the context."""
        # Get the data for the member, and set it in the context
        results = get_member_data(
            self.request.user,
            kwargs.get('object'),
            self.default_resource_name,
            self.default_record_type
        )
        kwargs.setdefault('results', results)
        return super().get_context_data(**kwargs)


class DataSourcesView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Member
    template_name = "data_sources.html"

    def test_func(self):
        """
        The request.user may see the member's data sources if:
         - the request.user is the member, or
         - the request.user is in an Organization that has been granted access
           to the member's data
        """
        member = get_object_or_404(Member.objects.all(), pk=self.kwargs['pk'])
        if member.user != self.request.user:
            # The request.user is not the member. If the request.user is not in
            # an Organization that has been granted access to the member's data,
            # then return a 404 response.
            get_object_or_404(
                ResourceGrant.objects.filter(
                    organization__users=self.request.user),
                member_id=member.id
            )
        return True

    def get_context_data(self, **kwargs):
        """Add current data sources and data into the context."""
        context = super().get_context_data(**kwargs)
        available_sources = [{
            'provider': 'sharemyhealth',
            'name': 'Hixny',
            'image_url': static('images/icons/hixny.png')
        }]
        connected_source_providers = [
            source.provider for source in context['member'].user.social_auth.all()
        ]
        data_sources = [{
            'connected': source['provider'] in connected_source_providers,
            **source
        } for source in available_sources]
        context.setdefault('data_sources', data_sources)
        print("CONTEXT =", context)
        return context


class CreateMemberView(LoginRequiredMixin, CreateView):
    model = Member
    fields = ['user', 'birth_date', 'phone_number', 'address',
              'emergency_contact_name', 'emergency_contact_number']
    template_name = 'member.html'

    def get_success_url(self):
        return reverse_lazy('member:member-create')


class UpdateMemberView(LoginRequiredMixin, UpdateView):
    model = Member
    fields = ['birth_date', 'phone_number', 'address',
              'emergency_contact_name', 'emergency_contact_number']
    template_name = 'member.html'

    def get_success_url(self):
        member_id = self.object.id
        return reverse_lazy('member:member-update', kwargs={'pk': member_id})


class DeleteMemberView(LoginRequiredMixin, DeleteView):
    model = Member
    template_name = 'member_confirm_delete.html'
    success_url = reverse_lazy('org:dashboard')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "member/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add ResourceRequests for the user's resources to the context."""
        # Get all of the ResourceRequests for access to the self.request.user's
        # resources
        resource_requests = ResourceRequest.objects.filter(
            member=self.request.user
        ).order_by('-updated')[:4]
        organizations = self.request.user.member.organizations.all()[:4]
        kwargs.setdefault('resource_requests', resource_requests)
        kwargs.setdefault('organizations', organizations)
        id_token_payload = get_id_token_payload(self.request.user)
        kwargs.setdefault('id_token_payload', id_token_payload)
        return super().get_context_data(**kwargs)


@require_POST
@login_required(login_url='home')
def approve_resource_request(request, pk):
    """
    A view for a member to approve a ResourceRequest.

    Approving a ResourceRequest means setting its status to 'Approved', and
    creating a ResourceGrant.
    """
    # Is the ResourceRequest for this member?
    resource_request = get_object_or_404(
        ResourceRequest.objects.filter(member=request.user),
        pk=pk
    )
    resource_request.status = REQUEST_APPROVED
    resource_request.save()
    # The ResourceRequest is for this member, so create a ResourceGrant for it
    ResourceGrant.objects.create(
        organization=resource_request.organization,
        member=resource_request.member,
        resource_class_path=resource_request.resource_class_path,
        resource_request=resource_request
    )
    return redirect(reverse('member:dashboard'))


@require_POST
@login_required(login_url='home')
def revoke_resource_request(request, pk):
    """
    A view for a member to revoke access to a resource (after an approved ResourceRequest).

    Revoking a ResourceRequest means setting its status to 'Denied', and
    deleting the related ResourceGrant.
    """
    # Is the ResourceRequest for this member?
    resource_request = get_object_or_404(
        ResourceRequest.objects.filter(member=request.user),
        pk=pk
    )
    # The ResourceRequest is for this member; set its status to REQUEST_DENIED.
    resource_request.status = REQUEST_DENIED
    resource_request.save()
    # The ResourceRequest is for this member, so delete the relevant
    # ResourceGrant
    if getattr(resource_request, 'resourcegrant', None):
        resource_request.resourcegrant.delete()
    return redirect(reverse('member:dashboard'))
