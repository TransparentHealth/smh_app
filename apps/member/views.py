import json
from datetime import datetime, timezone, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http.response import HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.views.generic.base import View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from memoize import delete_memoized
from .constants import RECORDS
from .models import Member
from .utils import fetch_member_data, get_resource_data, get_prescriptions, get_allergies
from apps.data.util import parse_timestamp
from apps.org.models import (
    Organization,
    ResourceGrant,
    ResourceRequest,
    RESOURCE_CHOICES,
    REQUEST_REQUESTED,
    REQUEST_APPROVED,
    REQUEST_DENIED,
)
from apps.users.models import UserProfile
from apps.notifications.models import Notification
from .forms import ResourceRequestForm
from .utils import get_id_token_payload


class SelfOrApprovedOrgMixin(UserPassesTestMixin):

    def get_login_url(self):
        """Org agents can request access, others go home (login or member:dashboard)."""
        if not self.request.user.is_anonymous and self.request.user.userprofile.user_type == 'O':
            return reverse('member:request-access', args=[self.kwargs['pk']])
        else:
            return reverse('login') + '?next=' + self.request.path

    def handle_no_permission(self):
        return redirect(self.get_login_url())

    def test_func(self):
        """
        The request.user may see the member's data sources if:
         - the request.user is the member, or
         - the request.user is in an Organization that has been granted access
           to the member's data
        """
        member = get_object_or_404(Member.objects.filter(pk=self.kwargs['pk']))
        if member.user != self.request.user:
            # The request.user is not the member. If the request.user is not in
            # an Organization that has been granted access to the member's data,
            # then return False.
            resource_grant = ResourceGrant.objects.filter(
                organization__users=self.request.user, member=member.user
            ).first()
            if not resource_grant:
                return False
        return True


class SummaryView(LoginRequiredMixin, SelfOrApprovedOrgMixin, DetailView):
    model = Member
    template_name = "summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the data for the member, and set it in the context
        data = fetch_member_data(context['member'], 'sharemyhealth')
        if settings.DEBUG:
            context['data'] = data
        if data is None or 'entry' not in data or not data['entry']:
            delete_memoized(
                fetch_member_data,
                context['member'],
                'sharemyhealth')

        # put the current resources in the summary tab.  We will not show the
        # other options in this tab.
        conditions_data = get_resource_data(data, 'Condition')
        prescription_data = get_prescriptions(data)

        all_records = RECORDS
        summarized_records = []
        notes_headers = ['Agent Name', 'Organization', 'Date']
        for record in all_records:
            # adding data for each resourceType in response from endpoint
            if record['name'] == 'Diagnoses':
                record['count'] = len(conditions_data)
                record['data'] = conditions_data
                summarized_records.append(record)

            if record['name'] == 'Prescriptions':
                record['count'] = len(prescription_data)
                record['data'] = prescription_data
                summarized_records.append(record)

            context.setdefault('summarized_records', summarized_records)

        context.setdefault('notes_headers', notes_headers)
        # TODO: include notes in the context data.

        return context


class RecordsView(LoginRequiredMixin, SelfOrApprovedOrgMixin, DetailView):
    model = Member
    template_name = "records.html"
    default_resource_name = 'sharemyhealth'
    default_record_type = 'Condition'

    def get_context_data(self, **kwargs):
        """Add records data into the context."""
        context = super().get_context_data(**kwargs)
        member = context['member']
        resource_name = self.kwargs.get('resource_name') or 'list'

        # Get the data for the member, and set it in the context
        data = fetch_member_data(member, 'sharemyhealth')

        if settings.DEBUG:
            context['data'] = data
        if data is None or 'entry' not in data or not data['entry']:
            delete_memoized(fetch_member_data, member, 'sharemyhealth')

        if resource_name == 'list':
            conditions_data = get_resource_data(data, 'Condition')
            observation_data = get_resource_data(data, 'Observation')
            encounter_data = get_resource_data(data, 'Encounter')
            prescription_data = get_prescriptions(data)
            allergies = get_allergies(data, keys=['id'])
            all_records = RECORDS
            for record in all_records:
                # adding data for each resoureType in response from
                # endpoint
                if record['name'] == 'Diagnoses':
                    record['count'] = len(conditions_data)
                    record['data'] = conditions_data

                if record['name'] == 'Lab Results':
                    record['count'] = len(observation_data)
                    record['data'] = observation_data

                if record['name'] == 'Prescriptions':
                    record['count'] = len(prescription_data)
                    record['data'] = prescription_data

                if record['name'] == 'Procedures':
                    record['count'] = len(encounter_data)
                    record['data'] = encounter_data

                if record['name'] == 'Allergies':
                    record['count'] = len(allergies)
                    record['data'] = allergies

            context.setdefault('all_records', all_records)

        elif resource_name == 'diagnoses':
            conditions_data = get_resource_data(data, 'Condition')
            headers = ['Date', 'Code', 'Diagnosis', 'Provider']
            diagnoses = []
            for condition in conditions_data:
                diagnosis = dict(
                    Date=(
                        condition.get('assertedDate')
                        and parse_timestamp(condition['assertedDate'])
                        or None
                    ),
                    Code=condition['code']['coding'][0].get('code', None),
                    Diagnosis=condition['code']['coding'][0].get('display', None),
                    Provider=condition.get('provider', None),
                )
                diagnoses.append(diagnosis)

            # sort diagnoses in order of date descending
            diagnoses.sort(
                key=lambda d: d['Date'] or datetime(
                    1, 1, 1), reverse=True)

            context.setdefault('title', 'Diagnoses')
            context.setdefault('headers', headers)
            context.setdefault('content_list', diagnoses)

        elif resource_name == 'lab-results':
            observation_data = get_resource_data(data, 'Observation')
            headers = ['Date', 'Code', 'Lab Result', 'Value']
            lab_results = []
            for observation in observation_data:
                lab = dict(
                    Date=(
                        observation.get(
                            'effectivePeriod',
                            {}).get('start') and parse_timestamp(
                            observation['effectivePeriod']['start']) or None),
                    Code=observation['code']['coding'][0].get(
                        'code',
                        None),
                    Display=observation['code']['coding'][0].get(
                        'display',
                        None),
                )
                lab_value = observation.get('valueQuantity', None)
                lab['Value'] = (
                    str(list(lab_value.values())[0]) + list(lab_value.values())[1]
                    if lab_value
                    else None
                )
                lab_results.append(lab)

            # sort lab_results in order of date descending
            lab_results.sort(
                key=lambda d: d['Date'] or datetime(
                    1, 1, 1), reverse=True)

            context.setdefault('title', 'Lab Results')
            context.setdefault('headers', headers)
            context.setdefault('content_list', lab_results)

        elif resource_name == 'procedures':
            encounter_data = get_resource_data(data, 'Encounter')
            headers = ['Date', 'Type', 'Practitioner', 'Location']
            procedures = []
            for encounter in encounter_data:
                procedure = dict(
                    Date=(
                        encounter.get('period', {}).get('start')
                        and parse_timestamp(encounter['period']['start'])
                        or None
                    ),
                    Type=encounter['type'][0]['text'],
                    Practitioner=', '.join(
                        [
                            participant['individual']['display']
                            for participant in encounter.get('participant', [])
                            if 'Practitioner' in participant['individual']['reference']
                        ]
                    ),
                    Location=encounter['location'][0]['location']['display'],
                )
                procedures.append(procedure)

            # sort procedures in order of date descending
            procedures.sort(
                key=lambda d: d['Date'] or datetime(
                    1, 1, 1), reverse=True)

            context.setdefault('title', 'Procedures')
            context.setdefault('headers', headers)
            context.setdefault('content_list', procedures)

        elif resource_name == 'prescriptions':
            prescription_data = get_prescriptions(data)
            headers = ['Date', 'Medication', 'Provider(s)']
            all_records = []

            # sort prescriptions by start date descending
            med_names = [
                np[0]
                for np in sorted(
                    [(name, prescription) for name, prescription in prescription_data.items()],
                    key=lambda np: np[1]['statements']
                    and np[1]['statements'][0].effectivePeriod.start
                    or datetime(1, 1, 1),
                    reverse=True,
                )
            ]
            # set up the display data
            for med_name in med_names:
                prescription = prescription_data[med_name]
                record = {
                    'Date': prescription['statements']
                    and prescription['statements'][0].effectivePeriod.start
                    or None,
                    'Medication': med_name,
                    'Provider(s)': ', '.join(
                        [request.requester.agent.display for request in prescription['requests']]
                    ),
                }
                record['links'] = {
                    'Medication': f'/member/{member.id}/modal/prescription/{prescription["medication"].id}'
                }
                all_records.append(record)

            context.setdefault('title', 'Prescriptions')
            context.setdefault('headers', headers)
            context.setdefault('content_list', all_records)

        elif resource_name == 'allergies':
            allergies = get_allergies(
                data,
                keys=['id', 'assertedDate', 'code']
                + ['clinicalStatus', 'verificationStatus', 'reaction'],
            )
            headers = [
                'Asserted',
                'Code',
                'Status',
                'Verification',
                'Reaction']
            default_timestamp = datetime(
                1, 1, 1, tzinfo=timezone(timedelta(0)))
            all_records = sorted(
                [
                    {
                        'Asserted': allergy.assertedDate,
                        'Code': allergy.code.text,
                        'Status': allergy.clinicalStatus.text,
                        'Verification': allergy.verificationStatus.text,
                        'Reaction': ', '.join(
                            [
                                ', '.join([manifestation.text for manifestation in manifestations])
                                for manifestations in [
                                    reaction.manifestation for reaction in allergy.reaction
                                ]
                            ]
                        ),
                    }
                    for allergy in allergies
                ],
                key=lambda r: r.get('Asserted') or default_timestamp,
                reverse=True,
            )
            context.setdefault('title', 'Allergies')
            context.setdefault('headers', headers)
            context.setdefault('content_list', all_records)

        return context

    def render_to_response(self, context, **kwargs):
        if context.get('redirect_url'):
            return redirect(context.get('redirect_url'))
        else:
            return super().render_to_response(context, **kwargs)


class PrescriptionDetailModalView(
        LoginRequiredMixin,
        SelfOrApprovedOrgMixin,
        TemplateView):
    """modal (bare) HTML for a single prescription"""

    template_name = "member/prescription_modal_content.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = get_object_or_404(
            Member.objects.filter(pk=kwargs['pk']))
        member_data = fetch_member_data(context['member'], 'sharemyhealth')
        if settings.DEBUG:
            context['data'] = member_data
        prescriptions = get_prescriptions(
            member_data,
            id=context['resource_id'],
            incl_practitioners=True,
            json=True)
        if not prescriptions:
            return Http404()
        else:
            context['prescription'] = next(iter(prescriptions.values()))
            return context


class DataView(LoginRequiredMixin, SelfOrApprovedOrgMixin, View):
    """Return JSON containing the requested member data."""

    def get(self, request, *args, **kwargs):
        member = get_object_or_404(Member.objects.filter(pk=kwargs['pk']))
        resource_type = kwargs['resource_type']
        resource_id = kwargs['resource_id']
        member_data = fetch_member_data(member, 'sharemyhealth')
        if resource_type == 'prescriptions':
            data = get_prescriptions(
                member_data, id=resource_id, incl_practitioners=True, json=True
            )
        else:
            # fallback
            data = {
                resource['id']: resource
                for resource in get_resource_data(
                    member_data, kwargs['resource_type'], id=resource_id
                )
            }
        return JsonResponse(data)


class ProvidersView(LoginRequiredMixin, SelfOrApprovedOrgMixin, DetailView):
    model = Member
    template_name = "providers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = fetch_member_data(context['member'], 'sharemyhealth')
        if settings.DEBUG:
            context['data'] = data
        if data is None or 'entry' not in data or not data['entry']:
            delete_memoized(
                fetch_member_data, 
                context['member'],
                'sharemyhealth')

        # if in the future we need more info
        # location_data = get_resource_data(data, 'Location')
        # provider_data = get_resource_data(data, 'Practitioner')

        # encounter resourceType seems to hold enough info to show provider
        # name, location name and date of visit info
        encounter_data = get_resource_data(data, 'Encounter')
        providers_headers = ['Doctor’s Name', 'Clinic', 'Date Last Seen']

        providers = []
        for encounter in encounter_data:
            if 'participant' not in encounter:
                continue
            provider = {}
            provider[
                'doctor-name'] = encounter['participant'][0]['individual']['display']
            provider['clinic'] = encounter[
                'location'][0]['location']['display']
            provider[
                'date-last-seen'] = parse_timestamp(encounter['period']['start'])
            providers.append(provider)

            # A way to get more provider info from provider_data
            # provider_id = encounter['participant'][0]['individual']['reference'].split('/')[1]
            # [provider for provider in provider_data if provider['id'] == provider_id][0]

            # A way to get more location info from location_data
            # location_id = encounter['location'][0]['location']['reference'].split('/')[1]
            # [location for location in location_data if location['id'] == location_id][0]

        providers.sort(key=lambda p: p['date-last-seen'], reverse=True)

        context.setdefault('providers_headers', providers_headers)
        context.setdefault('providers', providers)

        return context


class DataSourcesView(LoginRequiredMixin, SelfOrApprovedOrgMixin, DetailView):
    model = Member
    template_name = "data_sources.html"

    def get_context_data(self, **kwargs):
        """Add current data sources and data into the context."""
        context = super().get_context_data(**kwargs)
        available_sources = [
            {
                'provider': 'sharemyhealth',
                'name': 'Hixny',
                'image_url': static('images/icons/hixny.png'),
            }
        ]
        connected_source_providers = [
            source.provider for source in context['member'].user.social_auth.all()]
        data_sources = [
            {'connected': source['provider'] in connected_source_providers, **source}
            for source in available_sources
            if source['provider']
        ]
        context.setdefault('data_sources', data_sources)
        return context


class OrganizationsView(
        LoginRequiredMixin,
        SelfOrApprovedOrgMixin,
        DetailView):
    model = Member
    template_name = "member/organizations.html"

    def get_context_data(self, **kwargs):
        """Add organizations data into the context."""
        context = super().get_context_data(**kwargs)
        orgs = Organization.objects.all().order_by('name')
        resources = ResourceRequest.objects.filter(
            member=context['member'].user)
        current = [
            r.organization for r in resources if r.status == REQUEST_APPROVED]
        requested = [
            r.organization for r in resources if r.status == REQUEST_REQUESTED]
        available = [
            org for org in orgs if org not in current and org not in requested]
        context['organizations'] = {
            'current': current,
            'requested': requested,
            'available': available,
        }
        return context


class RequestAccessView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = 'member/request_access.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = context['member']
        member_requests = ResourceRequest.objects.filter(member=member.user)
        member_connected_orgs = [
            rr.organization for rr in member_requests if rr.status == REQUEST_APPROVED]
        member_requested_orgs = [
            rr.organization for rr in member_requests if rr.status == REQUEST_REQUESTED]
        orgs = self.request.user.organization_set.all()  # Orgs this user is agent for
        current = [org for org in orgs if org in member_connected_orgs]
        requested = [org for org in orgs if org in member_requested_orgs]
        available = [
            org for org in orgs if org not in member_connected_orgs +
            member_requested_orgs]
        context['organizations'] = {
            'current': current,
            'requested': requested,
            'available': available,
        }
        return context


class CreateMemberView(LoginRequiredMixin, CreateView):
    model = Member
    fields = [
        'user',
        'birth_date',
        'phone_number',
        'address',
        'emergency_contact_name',
        'emergency_contact_number',
    ]
    template_name = 'member.html'

    def get_success_url(self):
        return reverse_lazy('member:member-create')


class UpdateMemberView(LoginRequiredMixin, SelfOrApprovedOrgMixin, UpdateView):
    model = Member
    fields = [
        'phone_number',
        'address',
        'emergency_contact_name',
        'emergency_contact_number']
    template_name = 'member.html'

    def get_success_url(self):
        member_id = self.object.id
        return reverse_lazy('member:member-update', kwargs={'pk': member_id})

    def get_context_data(self, **kwargs):
        id_token_payload = get_id_token_payload(self.request.user)
        kwargs.setdefault('id_token_payload', id_token_payload)
        return super().get_context_data(**kwargs)


class DeleteMemberView(LoginRequiredMixin, DeleteView):
    model = Member
    template_name = 'member_confirm_delete.html'
    success_url = reverse_lazy('org:dashboard')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "member/dashboard.html"

    def get_context_data(self, **kwargs):
        notifications = Notification.objects.filter(
            notify_id=self.request.user.id, dismissed=False
        ).order_by('-created')[:4]
        organizations = [
            resource_grant.organization
            for resource_grant in self.request.user.resourcegrant_set.all()
        ][:4]
        kwargs.setdefault('notifications', notifications)
        kwargs.setdefault('organizations', organizations)
        id_token_payload = get_id_token_payload(self.request.user)
        kwargs.setdefault('id_token_payload', id_token_payload)
        return super().get_context_data(**kwargs)


@login_required(login_url='home')
def redirect_subject_url_to_member(request, subject, rest=''):
    """If one of the above member views is given with subject_id (== 15 digits),
    interpret it as the UserProfile.subject and redirect to the corresponding pk URL
    """
    try:
        user_profile = UserProfile.objects.get(subject=subject)
    except UserProfile.DoesNotExist:
        raise Http404('Member does not exist')
    pk = user_profile.user.member.pk
    url = f"/member/{pk}/{rest}"
    return redirect(url)


class NotificationsView(LoginRequiredMixin, TemplateView):
    template_name = "member/notifications.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = Notification.objects.filter(
            notify_id=self.request.user.id, dismissed=False
        ).order_by('-created')
        context.setdefault('notifications', notifications)
        return context


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
        ResourceRequest.objects.filter(
            member=request.user), pk=pk)
    resource_request.status = REQUEST_APPROVED
    resource_request.save()

    # The ResourceRequest is for this member, so create a ResourceGrant for it
    ResourceGrant.objects.create(
        organization=resource_request.organization,
        member=resource_request.member,
        resource_class_path=resource_request.resource_class_path,
        resource_request=resource_request,
    )

    if request.GET.get('next'):
        return redirect(request.GET['next'])
    else:
        return redirect(reverse('member:dashboard'))


@require_POST
@login_required(login_url='home')
def revoke_resource_request(request, pk):
    """
    A view for a member to revoke access to a resource
    (either before or after an approved ResourceRequest).

    Revoking a ResourceRequest means setting its status to 'Denied', and
    deleting the related ResourceGrant, if any.
    """
    # Is the ResourceRequest for this member?
    resource_request = get_object_or_404(
        ResourceRequest.objects.filter(
            member=request.user), pk=pk)

    # The ResourceRequest is for this member; set its status to REQUEST_DENIED.
    resource_request.status = REQUEST_DENIED
    resource_request.save()

    # The ResourceRequest is for this member, so delete the relevant
    # ResourceGrant, if any
    if getattr(resource_request, 'resourcegrant', None):
        resource_request.resourcegrant.delete()

    if request.GET.get('next'):
        return redirect(request.GET['next'])
    else:
        return redirect(reverse('member:dashboard'))


@require_POST
@login_required(login_url='home')
def resource_request_response(request):
    """
    A member can directly create a ResourceGrant to an organization who has not requested it.
    This requires having both the 'member' and the 'organization' ids in the POST data.
    """
    if request.POST.get('approve'):
        status = REQUEST_APPROVED
    elif request.POST.get('deny') or request.POST.get('revoke'):
        status = REQUEST_DENIED
    elif request.POST.get('requested'):
        status = REQUEST_REQUESTED
    else:
        status = None
    form = ResourceRequestForm(
        {
            'user': request.user.id,
            'status': status,
            'resource_class_path': RESOURCE_CHOICES[0][0],
            'member': request.POST.get('member'),
            'organization': request.POST.get('organization'),
        }
    )
    if form.is_valid() and (
        form.cleaned_data['member'] == request.user
        or (
            form.cleaned_data['organization'] in request.user.organization_set.all()
            and form.cleaned_data['status'] in [REQUEST_DENIED, REQUEST_REQUESTED]
        )
    ):
        resource_request = ResourceRequest.objects.filter(
            member=form.cleaned_data['member'],
            organization=form.cleaned_data['organization'],
            resource_class_path=form.cleaned_data['resource_class_path'],
        ).first()
        if resource_request is None:
            resource_request = ResourceRequest.objects.create(
                member=form.cleaned_data['member'],
                organization=form.cleaned_data['organization'],
                resource_class_path=form.cleaned_data['resource_class_path'],
                user=request.user,
            )
        resource_request.status = form.cleaned_data['status']
        resource_request.save()

        if resource_request.status == REQUEST_DENIED:
            # delete any existing ResourceGrant objects associated with this
            # request
            ResourceGrant.objects.filter(
                member=resource_request.member,
                organization=resource_request.organization,
                resource_class_path=resource_request.resource_class_path,
                resource_request=resource_request,
            ).delete()
        elif resource_request.status == REQUEST_APPROVED:
            # make sure there is a ResourceGrant object associated with this
            # ResourceRequest
            ResourceGrant.objects.get_or_create(
                member=resource_request.member,
                organization=resource_request.organization,
                resource_class_path=resource_request.resource_class_path,
                resource_request=resource_request,
            )
    else:
        return HttpResponse(json.dumps(form.errors), status=422)

    if request.GET.get('next'):
        return redirect(request.GET['next'])
    else:
        return redirect(reverse('home'))
