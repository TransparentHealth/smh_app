from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, Http404, render, redirect, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView

import requests
import json

from .models import Member
from .constants import RECORDS
from apps.org.models import (
    ResourceGrant, ResourceRequest, REQUEST_APPROVED, REQUEST_DENIED, REQUEST_REQUESTED
)
from smh_app.utils import get_vmi_user_detail, update_vmi_user_detail


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return get_fake_context_data(context)


class DataSourcesView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "data_sources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return get_fake_context_data(context)


class CreateMemberView(LoginRequiredMixin, CreateView):
    model = Member
    fields = ['user', 'birth_date', 'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_number']
    template_name = 'member.html'

    def get_success_url(self):
        member_id = self.object.id
        return reverse_lazy('member:member-detail', kwargs={'pk': member_id})


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = 'member.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_uid = context['member'].social_auth.values().first()['uid']
        context['user_data'] = get_vmi_user_detail(context['view'].request, member_uid).json()
        return context

    def post(self, request, *args, **kwargs):
        member_uid = Member.objects.get(pk=kwargs['pk']).social_auth.values().first()['uid']
        response = update_vmi_user_detail(request, member_uid)
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)

        if response.status_code == 200:
            context['user_data'] = json.loads(response.content)

        if response.status_code == 400:
            # setting the posted data as default 'user_data' in the context
            context['user_data'] = {key: value[0] for (key, value) in dict(request.POST).items()}
            context['errors'] = json.loads(response.content)

        # TODO: Add other response types: 403, 500

        return self.render_to_response(context=context)


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

    Approving a ResourceRequest means settings its status to 'Approved', and
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

    Revoking a ResourceRequest means settings its status to 'Denied', and
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


@login_required(login_url='home')
def get_member_data(request, pk, resource_name, record_type):
    # Get the path to the resource class from the settings, based on the resource_name.
    resource_class_path = settings.RESOURCE_NAME_AND_CLASS_MAPPING.get(resource_name, None)
    # If there is not a path for the resource_name, raise an error
    if not resource_class_path:
        raise Http404

    # Is the record_type is not valid, raise an error
    if record_type not in settings.VALID_MEMBER_DATA_RECORD_TYPES:
        raise Http404

    # Does the request.user's Organization have access to this member's resource?
    resource_grant = get_object_or_404(
        ResourceGrant.objects.filter(
            member_id=pk,
            resource_class_path=resource_class_path,
            organization__users=request.user
        )
    )

    data = resource_grant.resource_class(resource_grant.member).get(record_type)
    return render(request, 'member/data.html', context={'data': data})
