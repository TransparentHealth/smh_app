import requests
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView

from .constants import RECORDS
from .models import Member
from .utils import get_member_data, api_call, get_resource_data
from apps.org.models import (
    ResourceGrant, ResourceRequest, REQUEST_APPROVED, REQUEST_DENIED
)


class RecordsView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "records.html"
    default_resource_name = 'sharemyhealth'
    default_record_type = 'Condition'

    def get_context_data(self, **kwargs):
        """Add records data into the context."""
        # Get the data for the member, and set it in the context

        # a potentially more legit way to get data from alpha.sharemyhealth
        # results = get_member_data(
        #     self.request.user,
        #     kwargs.get('object'),
        #     self.default_resource_name,
        #     self.default_record_type
        # )

        # a less legit way to get data from test_data
        data = api_call()
        if self.kwargs['resource_name'] == 'list':
            conditions_data = get_resource_data(data, 'Condition')
            observation_data = get_resource_data(data, 'Observation')
            all_records = RECORDS
            for record in all_records:
            # adding data for each resoureType in response from endpoint
                if record['name'] == 'Diagnoses':
                    record['count'] = len(conditions_data)
                    record['data'] = conditions_data

                if record['name'] == 'Lab Results':
                    record['count'] = len(observation_data)
                    record['data'] = observation_data

                kwargs.setdefault('all_records', all_records)

        elif self.kwargs['resource_name'] == 'diagnoses':
            conditions_data = get_resource_data(data, 'Condition')
            headers = ['Date', 'Code', 'Diagnosis', 'Provider']
            all_diagnoses = []
            for condition in conditions_data:
                diagnoses = {}
                diagnoses['Date'] = condition.get('assertedDate', '-')
                diagnoses['Code'] = condition['code']['coding'][0].get('code', '-')
                diagnoses['Diagnosis'] = condition['code']['coding'][0].get('display', '-')
                diagnoses['Provider'] = condition.get('provider', '-')
                all_diagnoses.append(diagnoses)

            kwargs.setdefault('title', 'Diagnoses')
            kwargs.setdefault('headers', headers)
            kwargs.setdefault('content_list', all_diagnoses)

        elif self.kwargs['resource_name'] == 'lab-results':
            observation_data = get_resource_data(data, 'Observation')
            headers = ['Date', 'Code', 'Lab Result', 'Value']
            all_labs = []
            for observation in observation_data:
                lab = {}
                lab['Date'] = observation['effectivePeriod'].get('start', '-').split('T')[0]
                lab['Code'] = observation['code']['coding'][0].get('code', '-')
                lab['Display'] = observation['code']['coding'][0].get('display', '-')
                lab_value = observation.get('valueQuantity', None)
                lab['Value'] = str(list(lab_value.values())[0]) + list(lab_value.values())[1] if lab_value else '-'  # observation['valueQuantity'].get('value', '-') + observation['valueQuantity'].get('unit', '-')

                all_labs.append(lab)

            kwargs.setdefault('title', 'Lab Results')
            kwargs.setdefault('headers', headers)
            kwargs.setdefault('content_list', all_labs)

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
                ResourceGrant.objects.filter(organization__users=self.request.user),
                member_id=member.id
            )
        return True

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

        return super().get_context_data(**kwargs)


class CreateMemberView(LoginRequiredMixin, CreateView):
    model = Member
    fields = ['user', 'birth_date', 'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_number']
    template_name = 'member.html'

    def get_success_url(self):
        return reverse_lazy('member:member-create')


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
        ).order_by('-updated')[:4]
        organizations = self.request.user.member.organizations.all()[:4]
        kwargs.setdefault('resource_requests', resource_requests)
        kwargs.setdefault('organizations', organizations)
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
