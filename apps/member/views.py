import json
import logging
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.templatetags.static import static
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.urls import reverse_lazy
from django.utils.html import mark_safe
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import DeleteView
from memoize import delete_memoized

from apps.data.models.condition import Condition
from apps.data.models.encounter import Encounter
from apps.data.models.procedure import Procedure
from apps.data.models.observation import Observation
from apps.data.models.practitioner import Practitioner
from apps.data.util import parse_timestamp
from apps.notifications.models import Notification
from apps.org.models import (
    REQUEST_APPROVED,
    REQUEST_DENIED,
    REQUEST_REQUESTED,
    RESOURCE_CHOICES,
    Organization,
    ResourceGrant,
    ResourceRequest,
)
from apps.users.models import UserProfile
from apps.users.utils import get_id_token_payload

from .constants import RECORDS
from .forms import ResourceRequestForm
from .utils import (
    fetch_member_data,
    get_allergies,
    get_prescriptions,
    get_resource_data,
)

logger = logging.getLogger(__name__)


class SelfOrApprovedOrgMixin(UserPassesTestMixin):

    def get_login_url(self):
        """Org agents can request access, others go home (login or member:dashboard)."""
        if (
            not self.request.user.is_anonymous
            and self.request.user.user_type == self.request.user.UserType.ORG_AGENT
        ):
            return reverse('member:request-access', args=[self.kwargs['pk']])
        else:
            return reverse('login') + '?next=' + self.request.path

    def handle_no_permission(self):
        return redirect(self.get_login_url())

    def get_member(self):
        return get_object_or_404(get_user_model().objects.filter(pk=self.kwargs['pk']))

    def test_func(self):
        """
        The request.user may see the member's data sources if:
         - the request.user is the member, or
         - the request.user is in an Organization that has been granted access
           to the member's data
        """
        member = self.get_member()
        if member != self.request.user:
            # The request.user is not the member. If the request.user is not in
            # an Organization that has been granted access to the member's data,
            # then return False.
            resource_grant = ResourceGrant.objects.filter(
                organization__agents=self.request.user, member=member
            ).first()
            if not resource_grant:
                return False
        return True


class SummaryView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        # Get the data for the member, and set it in the context
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        if context['updated_at']:
            context['time_since_update'] = (
                datetime.now(timezone.utc) - context['updated_at']
            )
        fhir_data = data.get('fhir_data')
        if settings.DEBUG:
            context['data'] = data

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        # put the current resources in the summary tab.  We will not show the
        # other options in this tab.
        conditions_data = get_resource_data(fhir_data, 'Condition')
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


class RecordsView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "records.html"
    default_resource_name = 'sharemyhealth'
    default_record_type = 'Condition'

    def get_context_data(self, **kwargs):
        """Add records data into the context."""
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        resource_name = self.kwargs.get('resource_name') or 'list'

        # Get the data for the member, and set it in the context
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        if context['updated_at']:
            context['time_since_update'] = (
                datetime.now(timezone.utc) - context['updated_at']
            )
        fhir_data = data.get('fhir_data')
        if settings.DEBUG:
            context['data'] = data

        logging.debug(
            "fhir_data records: %r",
            fhir_data and fhir_data.get(
                'entry') and len(fhir_data.get('entry')),
        )

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        if resource_name == 'list':
            conditions_data = get_resource_data(fhir_data, 'Condition')
            observation_data = get_resource_data(fhir_data, 'Observation')
            procedure_data = get_resource_data(fhir_data, 'Procedure')
            prescription_data = get_prescriptions(fhir_data)
            allergies = get_allergies(fhir_data, keys=['id'])
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
                    record['count'] = len(procedure_data)
                    record['data'] = procedure_data

                if record['name'] == 'Allergies':
                    record['count'] = len(allergies)
                    record['data'] = allergies

            context.setdefault('all_records', all_records)

        elif resource_name == 'diagnoses':
            conditions_data = get_resource_data(
                fhir_data, 'Condition', Condition.from_data
            )
            headers = ['Diagnosis', 'Status', 'Verification']
            diagnoses = sorted(
                [
                    dict(
                        Diagnosis=condition.code.text,
                        Status=condition.clinicalStatus,
                        Verification=condition.verificationStatus,
                    )
                    for condition in conditions_data
                ],
                key=lambda diagnosis: (
                    ['active', 'recurrence', 'inactive', 'remission', 'resolved'].index(
                        diagnosis['Status']
                    ),
                    diagnosis['Diagnosis'],
                ),
            )

            context.setdefault('title', 'Diagnoses')
            context.setdefault('headers', headers)
            context.setdefault('content_list', diagnoses)

        elif resource_name == 'lab-results':
            observation_data = get_resource_data(
                fhir_data, 'Observation', constructor=Observation.from_data
            )
            headers = ['Date', 'Code', 'Display', 'Lab Result']
            lab_results = sorted(
                [
                    {
                        'Date': observation.effectivePeriod.start,
                        'Code': (
                            observation.code.coding[0].code
                            if len(observation.code.coding) > 0
                            else None
                        ),
                        'Display': observation.code.text,
                        'Lab Result': observation.valueQuantity,
                    }
                    for observation in observation_data
                ],
                key=lambda observation: observation['Date']
                or datetime(1, 1, 1, tzinfo=timezone.utc),
                reverse=True,
            )

            context.setdefault('title', 'Lab Results')
            context.setdefault('headers', headers)
            context.setdefault('content_list', lab_results)

        elif resource_name == 'procedures':
            procedures_data = sorted(
                get_resource_data(
                    fhir_data, 'Procedure', constructor=Procedure.from_data
                ),
                key=lambda procedure: (
                    procedure.performedPeriod.start
                    or datetime(1, 1, 1, tzinfo=timezone.utc)
                ),
                reverse=True,
            )
            headers = ['Date', 'Status', 'Description', 'Provider']
            procedures = [
                {
                    'Date': procedure.performedPeriod.start,
                    'Status': procedure.status,
                    'Description': procedure.code.text,
                    'Provider': mark_safe(
                        '; '.join(
                            [
                                '<a class="modal-link" href="{url}">{name}</a>'.format(
                                    name=performer.actor.display,
                                    url=reverse_lazy(
                                        'member:provider_detail',
                                        kwargs={
                                            'pk': context['member'].id,
                                            'provider_id': performer.actor.id,
                                        },
                                    ),
                                )
                                for performer in procedure.performer
                                if 'Practitioner' in performer.actor.reference
                            ]
                        )
                    ),
                }
                for procedure in procedures_data
            ]

            context.setdefault('title', 'Procedures')
            context.setdefault('headers', headers)
            context.setdefault('content_list', procedures)

        elif resource_name == 'prescriptions':
            prescription_data = get_prescriptions(fhir_data)
            headers = ['Date', 'Medication', 'Provider(s)']
            all_records = []

            # sort prescriptions by start date descending
            med_names = [
                np[0]
                for np in sorted(
                    [
                        (name, prescription)
                        for name, prescription in prescription_data.items()
                    ],
                    key=lambda np: np[1]['statements']
                    and np[1]['statements'][0].effectivePeriod.start
                    or datetime(1, 1, 1, tzinfo=timezone.utc),
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
                        [
                            request.requester.agent.display
                            for request in prescription['requests']
                        ]
                    ),
                }
                record['links'] = {
                    'Medication': f"/member/{context['member'].id}"
                    + f"/modal/prescription/{prescription['medication'].id}"
                }
                all_records.append(record)

            context.setdefault('title', 'Prescriptions')
            context.setdefault('headers', headers)
            context.setdefault('content_list', all_records)

        elif resource_name == 'allergies':
            allergies = get_allergies(
                fhir_data,
                keys=['id', 'assertedDate', 'code']
                + ['clinicalStatus', 'verificationStatus', 'reaction'],
            )
            headers = ['Asserted', 'Code', 'Status',
                       'Verification', 'Reaction']
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
                                ', '.join(
                                    [
                                        manifestation.text
                                        for manifestation in manifestations
                                    ]
                                )
                                for manifestations in [
                                    reaction.manifestation
                                    for reaction in allergy.reaction
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
    LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView
):
    """modal (bare) HTML for a single prescription"""

    template_name = "member/prescription_modal_content.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        if context['updated_at']:
            context['time_since_update'] = (
                datetime.now(timezone.utc) - context['updated_at']
            )
        fhir_data = data.get('fhir_data')
        if settings.DEBUG:
            context['data'] = fhir_data

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        prescriptions = get_prescriptions(
            fhir_data, id=context[
                'resource_id'], incl_practitioners=True, json=True
        )
        if not prescriptions:
            return Http404()
        else:
            context['prescription'] = next(iter(prescriptions.values()))
            return context


class DataView(LoginRequiredMixin, SelfOrApprovedOrgMixin, View):
    """Return JSON containing the requested member data."""

    def get(self, request, *args, **kwargs):
        member = self.get_member()
        resource_type = kwargs['resource_type']
        resource_id = kwargs['resource_id']
        data = fetch_member_data(member, 'sharemyhealth')
        fhir_data = data.get('fhir_data')

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, member, 'sharemyhealth')

        if resource_type == 'prescriptions':
            response_data = get_prescriptions(
                fhir_data, id=resource_id, incl_practitioners=True, json=True
            )
        else:
            # fallback
            response_data = {
                resource['id']: resource
                for resource in get_resource_data(
                    fhir_data, kwargs['resource_type'], id=resource_id
                )
            }
        return JsonResponse(response_data)


class ProvidersView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "providers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        if context['updated_at']:
            context['time_since_update'] = (
                datetime.now(timezone.utc) - context['updated_at']
            )
        fhir_data = data.get('fhir_data')
        if settings.DEBUG:
            context['data'] = fhir_data

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        encounters = get_resource_data(
            fhir_data, 'Encounter', constructor=Encounter.from_data
        )
        encounters.sort(key=lambda e: e.period.start,
                        reverse=True)  # latest ones first
        practitioners = get_resource_data(
            fhir_data, 'Practitioner', constructor=Practitioner.from_data
        )
        for index, practitioner in enumerate(practitioners):
            practitioner.last_encounter = practitioner.next_encounter(
                encounters)
            practitioners[index] = practitioner

        practitioners.sort(
            key=lambda p: (
                p.last_encounter.period.start
                if p.last_encounter
                else datetime(1, 1, 1, tzinfo=timezone.utc)
            ),
            reverse=True,
        )

        context['practitioners'] = practitioners
        return context


class ProviderDetailView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "provider_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        if context['updated_at']:
            context['time_since_update'] = (
                datetime.now(timezone.utc) - context['updated_at']
            )
        fhir_data = data.get('fhir_data')

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        context['practitioner'] = next(
            iter(
                get_resource_data(
                    fhir_data,
                    'Practitioner',
                    constructor=Practitioner.from_data,
                    id=self.kwargs['provider_id'],
                )
            ),
            None,
        )
        if not context['practitioner']:
            raise Http404()

        prescriptions = [
            {
                'date': next(
                    iter(
                        sorted(
                            [
                                statement.period.start
                                for statement in prescription['statements']
                            ],
                            reverse=True,
                        )
                    ),
                    None,
                ),
                'type': 'Prescription',
                'display': prescription['medication'].code.text,
                'prescription': prescription,
            }
            for prescription in get_prescriptions(
                fhir_data, incl_practitioners=True
            ).values()
            if context['practitioner'].id in prescription['practitioners'].keys()
        ]
        procedures = [
            {
                'date': procedure.performedPeriod.start,
                'type': 'Procedure',
                'display': procedure.code.text,
                'procedure': procedure,
            }
            for procedure in get_resource_data(
                fhir_data, 'Procedure', constructor=Procedure.from_data
            )
        ]
        context['records'] = sorted(
            prescriptions + procedures,
            key=lambda r: r['date'] or datetime(1, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )

        return context


class DataSourcesView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "data_sources.html"

    def get_context_data(self, **kwargs):
        """Add current data sources and data into the context."""
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        available_sources = [
            {
                'provider': 'sharemyhealth',
                'name': 'Hixny',
                'image_url': static('images/icons/hixny.png'),
            }
        ]
        connected_source_providers = [
            source.provider for source in context['member'].social_auth.all()
        ]
        data_sources = [
            {'connected': source['provider'] in connected_source_providers, **source}
            for source in available_sources
            if source['provider']
        ]
        context.setdefault('data_sources', data_sources)
        return context


class OrganizationsView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "member/organizations.html"

    def get_context_data(self, **kwargs):
        """Add organizations data into the context."""
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        orgs = Organization.objects.all().order_by('name')
        resources = ResourceRequest.objects.filter(member=context['member'])
        current = [r.organization for r in resources if r.status ==
                   REQUEST_APPROVED]
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


class RequestAccessView(LoginRequiredMixin, TemplateView):
    template_name = 'member/request_access.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = get_object_or_404(
            get_user_model().objects.filter(pk=self.kwargs['pk'])
        )
        member_requests = ResourceRequest.objects.filter(
            member=context['member'])
        member_connected_orgs = [
            rr.organization for rr in member_requests if rr.status == REQUEST_APPROVED
        ]
        member_requested_orgs = [
            rr.organization for rr in member_requests if rr.status == REQUEST_REQUESTED
        ]
        orgs = (
            self.request.user.agent_organizations.all()
        )  # Orgs this user is agent for
        current = [org for org in orgs if org in member_connected_orgs]
        requested = [org for org in orgs if org in member_requested_orgs]
        available = [
            org
            for org in orgs
            if org not in member_connected_orgs + member_requested_orgs
        ]
        context['organizations'] = {
            'current': current,
            'requested': requested,
            'available': available,
        }
        return context


class ProfileView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = 'member.html'

    def get_success_url(self):
        member_id = self.object.id
        return reverse_lazy('member:member-profile', kwargs={'pk': member_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        return context


class DeleteMemberView(LoginRequiredMixin, SelfOrApprovedOrgMixin, DeleteView):
    model = get_user_model()
    template_name = 'member_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()

        # only open this method to the request.user on their own account
        if context['member'] != self.request.user:
            raise Http404('Account not found.')

        return context

    def get_success_url(self):
        return reverse('logout') + '?next=' + settings.REMOTE_ACCOUNT_DELETE_ENDPOINT


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "member/dashboard.html"

    def get_context_data(self, **kwargs):
        notifications = Notification.objects.filter(
            notify_id=self.request.user.id, dismissed=False
        ).order_by('-created')[:4]
        organizations = [
            resource_grant.organization
            for resource_grant in self.request.user.resource_grants.all()
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
    user_profile = get_object_or_404(UserProfile, subject=subject)
    return redirect(f"/member/{user_profile.user.id}/{rest}")


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
        ResourceRequest.objects.filter(member=request.user), pk=pk
    )
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
        ResourceRequest.objects.filter(member=request.user), pk=pk
    )

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
            form.cleaned_data[
                'organization'] in request.user.agent_organizations.all()
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


@require_POST
@login_required(login_url='home')
def refresh_member_data(request, pk):
    """Only allow members to refresh their own data"""
    member = get_object_or_404(get_user_model().objects.filter(pk=pk))
    if member == request.user:
        delete_memoized(fetch_member_data, member, 'sharemyhealth')
        fetch_member_data(member, 'sharemyhealth', refresh=True)
    else:
        print(
            "refresh not allowed: request.user %r != member %r" % (
                request.user, member)
        )

    if request.POST.get('next', None):
        return redirect(request.POST['next'])
    else:
        return redirect(reverse('member:records', member.id))
