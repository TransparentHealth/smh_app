from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from jwkest.jwt import JWT
from .constants import RECORDS
from .models import Member
from .utils import fetch_hixny_member_data, get_resource_data
from apps.org.models import (
    ResourceGrant, ResourceRequest, REQUEST_APPROVED, REQUEST_DENIED
)


def get_id_token_payload(user):
    # Get the ID Token and parse it.
    try:
        vmi = user.social_auth.filter(provider='vmi').first()
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


class SelfOrApprovedOrgMixin:
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


class RecordsView(LoginRequiredMixin, SelfOrApprovedOrgMixin, DetailView):
    model = Member
    template_name = "records.html"
    default_resource_name = 'sharemyhealth'
    default_record_type = 'Condition'

    def get_context_data(self, **kwargs):
        """Add records data into the context."""
        context = super().get_context_data(**kwargs)
        resource_name = self.kwargs.get('resource_name') or 'list'

        # Get the data for the member, and set it in the context
        data = fetch_hixny_member_data(context['member'])
        if data is not None:
            if resource_name == 'list':
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

                    context.setdefault('all_records', all_records)

            elif resource_name == 'diagnoses':
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

                context.setdefault('title', 'Diagnoses')
                context.setdefault('headers', headers)
                context.setdefault('content_list', all_diagnoses)

            elif resource_name == 'lab-results':
                observation_data = get_resource_data(data, 'Observation')
                headers = ['Date', 'Code', 'Lab Result', 'Value']
                all_labs = []
                for observation in observation_data:
                    lab = {}
                    lab['Date'] = observation['effectivePeriod'].get('start', '-').split('T')[0]
                    lab['Code'] = observation['code']['coding'][0].get('code', '-')
                    lab['Display'] = observation['code']['coding'][0].get('display', '-')
                    lab_value = observation.get('valueQuantity', None)
                    lab['Value'] = str(list(lab_value.values())[0]) + list(lab_value.values())[1] if lab_value else '-'
                    all_labs.append(lab)

                context.setdefault('title', 'Lab Results')
                context.setdefault('headers', headers)
                context.setdefault('content_list', all_labs)
        else:
            redirect_url = reverse('member:data-sources', kwargs={'pk': context['member'].user.pk})
            context.setdefault('redirect_url', redirect_url)

        return context

    def render_to_response(self, context, **kwargs):
        if context.get('redirect_url'):
            return redirect(context.get('redirect_url'))
        else:
            return super().render_to_response(context, **kwargs)


class DataSourcesView(LoginRequiredMixin, SelfOrApprovedOrgMixin, UserPassesTestMixin, DetailView):
    model = Member
    template_name = "data_sources.html"

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
