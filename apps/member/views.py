import requests

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView

from .constants import RECORDS
from .models import Member
from .utils import get_member_data
from apps.org.models import (
    ResourceGrant, ResourceRequest, REQUEST_APPROVED, REQUEST_DENIED, REQUEST_REQUESTED
)


def get_fake_context_data(context):
    # just-for-show data from fake endpoint, unrelated to any user/member/org.
    url_base = 'http://fhir-test.sharemy.health:8080/fhir/baseDstu3/'

    patient_id = '304'

    patient_url = url_base + 'Patient/' + patient_id
    patient_response = requests.get(url=patient_url)
    patient_data = patient_response.json()

    organization_url = url_base + patient_data['generalPractitioner'][0]['reference']
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
    default_record_type = 'all'

    def get_context_data(self, **kwargs):
        """Add records data into the context."""
        # Get the data for the member, and set it in the context
        data = get_member_data(
            self.request.user,
            kwargs.get('object'),
            self.default_resource_name,
            self.default_record_type
        )
        kwargs.setdefault('data', data)

        # TODO: remove this line, but keep it here for now until get_member_data()
        # returns meaningful data, so the template doesn't look blank.
        kwargs.setdefault('records_options', RECORDS)

        return super().get_context_data(**kwargs)


class DataSourcesView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "data_sources.html"
    default_record_type = 'all'

    def dispatch(self, request, *args, **kwargs):
        self.resource_name = kwargs.get('resource_name')
        self.record_type = kwargs.get('record_type') or self.default_record_type
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add current data sources and data into the context."""
        # Add current data sources into context
        current_data_sources = [
            {
                'resource_name': 'sharemyhealth',
                'image_url': static('images/icons/hixny.png')
            }
        ]
        kwargs.setdefault('current_data_sources', current_data_sources)

        # Get the data for this member
        if self.resource_name and self.record_type:
            data = get_member_data(
                self.request.user,
                kwargs.get('object'),
                self.resource_name,
                self.record_type
            )

            kwargs.setdefault('data', data)

        return super().get_context_data(**kwargs)


class CreateMemberView(LoginRequiredMixin, CreateView):
    model = Member
    fields = ['user', 'birth_date', 'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_number']
    template_name = 'member.html'

    def get_success_url(self):
        member_id = self.object.id
        return reverse_lazy('member:member-update', kwargs={'pk': member_id})


class UpdateMemberView(LoginRequiredMixin, UpdateView):
    model = Member
    fields = ['birth_date', 'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_number']
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
        # Get all of the ResourceRequests for access to the self.request.user's resources
        resource_requests = ResourceRequest.objects.filter(
            member=self.request.user
        ).filter(
            status=REQUEST_REQUESTED
        )
        resources_granted = ResourceRequest.objects.filter(
            member=self.request.user
        ).filter(
            status=REQUEST_APPROVED
        )
        kwargs.setdefault('resource_requests', resource_requests)
        kwargs.setdefault('resources_granted', resources_granted)
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
    # The ResourceRequest is for this member, so delete the relevant ResourceGrant
    if getattr(resource_request, 'resourcegrant', None):
        resource_request.resourcegrant.delete()
    return redirect(reverse('member:dashboard'))
