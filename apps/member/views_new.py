import json

import logging
# from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.templatetags.static import static
from django.http.response import Http404, HttpResponse   # , JsonResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.urls import reverse_lazy
# from django.utils.html import mark_safe
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import DeleteView
from memoize import delete_memoized

# from apps.data.models.condition import Condition
# from apps.data.models.encounter import Encounter
# from apps.data.models.procedure import Procedure
# from apps.data.models.observation import Observation
# from apps.data.models.practitioner import Practitioner
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

from .constants import RECORDS_STU3, FIELD_TITLES, RESOURCES
# , TIMELINE
# , PROVIDER_RESOURCES,
# , VITALSIGNS
from .forms import ResourceRequestForm
from .utils import (
     fetch_member_data
)
#     # get_allergies,
#     get_prescriptions,
#     get_resource_data,

from .fhir_requests import (
    get_converted_fhir_resource,
    get_lab_results,
    get_vital_signs,
)
from .fhir_utils import (
    resource_count,
    load_test_fhir_data,
    find_index,
    find_list_entry,
    path_extract,
    # sort_json,
    view_filter,
    groupsort,
    concatenate_lists,
    entry_check,
    context_updated_at,
    dated_bundle
)
from ..common.templatetags.fhirtags import resourceview
# from .practitioner_tools import practitioner_encounter, sort_extended_practitioner

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


class TimelineView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "timeline2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        # Get the data for the member, and set it in the context
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        context['timestamp'] = data.get('updated_at', "No timestamp")
        context = context_updated_at(context)
        return_to_view = "member:timeline"
        context.setdefault('return_to_view', return_to_view)

        ###
        # this will only pull a local fhir file if VPC_ENV is not prod|stage|dev
        fhir_data = load_test_fhir_data(data)
        # fhir_data = data.get('fhir_data')
        if settings.DEBUG:
            context['data'] = data
        #
        # get resource bundles
        #
        # resource_list = RESOURCES
        # Observation mixes lab results and vital signs
        # resource_list.remove('Observation')

        entries = get_converted_fhir_resource(fhir_data)
        # print('Resources:', len(entries['entry']))

        context.setdefault('resources', entries['entry'])

        counts = resource_count(entries['entry'])
        context.setdefault('counts', counts)
        #
        # print(counts)
        #
        #####
        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        # all_records = RECORDS
        all_records = RECORDS_STU3
        context.setdefault('all_headers', all_records)
        # summarized_records = []

        entries = dated_bundle(entries)
        # print(len(entries['entry']))
        context.setdefault('summarized_records', entries['entry'])

        return context


class SummaryView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        # Get the data for the member, and set it in the context
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        context['timestamp'] = data.get('updated_at', "No timestamp")
        context = context_updated_at(context)

        ###
        # this will only pull a local fhir file if VPC_ENV is not prod|stage|dev
        fhir_data = load_test_fhir_data(data)
        # fhir_data = data.get('fhir_data')
        if settings.DEBUG:
            context['data'] = data
        #
        # get resource bundles
        #
        resource_list = RESOURCES
        # Observation mixes lab results and vital signs
        resource_list.remove('Observation')

        resources = get_converted_fhir_resource(fhir_data)
        if len(resources.entry) > 0:
            resources = resources.entry
        else:
            resources = []
        context.setdefault('resources', resources)
        labs = get_lab_results(fhir_data)
        if len(labs.entry) > 0:
            labs = labs.entry
        else:
            labs = []
        context.setdefault('labs', labs)
        vitals = get_vital_signs(fhir_data)
        if len(vitals.entry) > 0:
            vitals = vitals.entry
        else:
            vitals = []
        context.setdefault('vitals', vitals)

        counts = resource_count(resources)
        context.setdefault('counts', counts)
        # print(counts)
        #
        #####
        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        # all_records = RECORDS
        all_records = RECORDS_STU3
        summarized_records = []
        notes_headers = ['Agent Name', 'Organization', 'Date']
        for record in all_records:

            if record['call_type'].lower() == "fhir":
                entries = get_converted_fhir_resource(fhir_data, record['resources'])
                record['data'] = entries['entry']
                record['count'] = len(entries['entry'])
                summarized_records.append(record)
            elif record['call_type'].lower() == 'custom':
                if record['name'] == 'VitalSigns':
                    entries = get_vital_signs(fhir_data)
                    record['data'] = entries['entry']
                    record['count'] = len(entries['entry'])
                    summarized_records.append(record)
                elif record['name'] == 'LabResults':
                    entries = get_lab_results(fhir_data)
                    record['data'] = entries['entry']
                    record['count'] = len(entries['entry'])
                    summarized_records.append(record)
            else:   # skip
                pass

        context.setdefault('summarized_records', summarized_records)

        context.setdefault('notes_headers', notes_headers)
        # TODO: include notes in the context data.

        return context


class RecordsView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "records2.html"
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
        context['timestamp'] = data.get('updated_at', "No timestamp")
        context = context_updated_at(context)
        return_to_view = "member:records"
        context.setdefault('return_to_view', return_to_view)

        ###
        # this will only pull a local fhir file if VPC_ENV is not prod|stage|dev
        fhir_data = load_test_fhir_data(data)
        # fhir_data = data.get('fhir_data')
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
            # all_records = RECORDS_STU3
            all_records = view_filter(RECORDS_STU3, 'record')
            summarized_records = []
            for record in all_records:
                if record['call_type'].lower() == "fhir":
                    # print("record processing for ", record['name'])
                    entries = get_converted_fhir_resource(fhir_data, record['resources'])
                    record['data'] = entries['entry']
                    record['count'] = len(entries['entry'])
                    summarized_records.append(record)
                elif record['call_type'].lower() == 'custom':
                    if record['name'] == 'VitalSigns':
                        entries = get_vital_signs(fhir_data, record)
                        record['data'] = entries['entry']
                        record['count'] = len(entries['entry'])
                        summarized_records.append(record)
                    elif record['name'] == 'LabResults':
                        entries = get_lab_results(fhir_data, record)
                        record['data'] = entries['entry']
                        record['count'] = len(entries['entry'])
                        summarized_records.append(record)
                else:  # skip
                    pass

            context.setdefault('all_records', summarized_records)

        else:
            resource_profile = RECORDS_STU3[find_index(RECORDS_STU3, "slug", resource_name)]

            # print("Resource Profile", resource_profile)

            if resource_profile:
                title = resource_profile['display']
                headers = resource_profile['headers']
                exclude = resource_profile['exclude']
                # second_fields = headers
                # second_fields.append(exclude)
            else:
                title = resource_name
                headers = ['id', '*']
                exclude = ['']
                # second_fields

            title = resource_profile['display']
            if resource_profile['call_type'] == 'custom':
                if resource_profile['slug'] == 'labresults':
                    entries = get_lab_results(fhir_data, resource_profile)
                elif resource_profile['slug'] == 'vitalsigns':
                    entries = get_vital_signs(fhir_data, resource_profile)
            elif resource_profile['call_type'] == 'skip':
                entries = {'entry': []}
            else:
                print("Get, sort, join")
                entries = get_converted_fhir_resource(fhir_data, [resource_profile['name']])
                # if resource_profile['name'] == "Procedure":
                print(len(entries['entry']))
                #     print("Procedures:", entries['entry'])
                # print(entries['entry'])
                entries = groupsort(entries['entry'], resource_profile)
                # if resource_profile['name'] == "Procedure":
                print(len(entries))
                #     print("Procedures - post sort:", entries['entry'])
                entries = concatenate_lists(entry_check(entries))
                # if resource_profile['name'] == "Procedure":
                print(len(entries['entry']))
                #     print("Procedures - post concatenate:", entries['entry'])

            content_list = path_extract(entries['entry'], resource_profile)
            context.setdefault('friendly_fields', find_list_entry(FIELD_TITLES, "profile", resource_profile['name']))
            context.setdefault('title', title)
            context.setdefault('headers', headers)
            context.setdefault('exclude', exclude)
            # context.setdefault('content_list', content_list)
            context.setdefault('resource_profile', resource_profile)
            # sorted_content = sort_json(content_list, sort_field)
            # context.setdefault('content_list', sorted_content)
            context.setdefault('content_list', content_list)

            print("Content_List:", content_list)
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
        context = context_updated_at(context)
        ###
        # this will only pull a local fhir file if VPC_ENV is not prod|stage|dev
        fhir_data = load_test_fhir_data(data)
        # fhir_data = data.get('fhir_data')
        if settings.DEBUG:
            context['data'] = fhir_data

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                            'member'], 'sharemyhealth')

        prescriptions = []
        # prescriptions = get_prescriptions(
        #     fhir_data, id=context[
        #         'resource_id'], incl_practitioners=True, json=True
        # )
        if not prescriptions:
            return Http404()
        else:
            context['prescription'] = next(iter(prescriptions.values()))
            return context


class DataView(LoginRequiredMixin, SelfOrApprovedOrgMixin, View):
    """Return JSON containing the requested member data."""

    def get(self, request, *args, **kwargs):
        member = self.get_member()
        print(member.pk)
        resource_type = kwargs['resource_type']
        resource_id = kwargs['resource_id']
        data = fetch_member_data(member, 'sharemyhealth')
        pretty = False
        pretty_text = request.GET.get('pretty')
        if pretty_text:
            if pretty_text.lower() == "true":
                pretty = True

        ###
        # this will only pull a local fhir file if VPC_ENV is not prod|stage|dev
        fhir_data = load_test_fhir_data(data)
        # fhir_data = data.get('fhir_data')

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, member, 'sharemyhealth')

        # if resource_type == 'prescriptions':
        #     response_data = get_prescriptions(
        #         fhir_data, id=resource_id, incl_practitioners=True, json=True
        #     )
        elif resource_type in RESOURCES:
            resource_profile = RECORDS_STU3[find_index(RECORDS_STU3, "slug", resource_type.lower())]
            if resource_profile:
                bundle = get_converted_fhir_resource(fhir_data, [resource_profile['name']])
                for entry in bundle['entry']:
                    if 'id' in entry:
                        if entry['id'] == resource_id:
                            data = entry
            if not pretty:
                response_data = json.dumps(data, indent=settings.JSON_INDENT)
            else:
                response_data = "<table>" + resourceview(data, member.pk) + "</table><hr/>"
                response_data += json.dumps(data, indent=settings.JSON_INDENT)
                # print(response_data)

            return HttpResponse(response_data)

        else:
            # fallback
            data = ["we shall show the pretty view for ", resource_type, "[", resource_id, "]"]
            response_data = resourceview()
            # print("httpResponse:", response_data, "-----")

        return HttpResponse(response_data)


class ProvidersView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "records2.html"
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
        context['timestamp'] = data.get('updated_at', "No timestamp")
        context = context_updated_at(context)
        return_to_view = "member:providers"
        context.setdefault('return_to_view', return_to_view)

        ###
        # this will only pull a local fhir file if VPC_ENV is not prod|stage|dev
        fhir_data = load_test_fhir_data(data)
        # fhir_data = data.get('fhir_data')
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
            # all_records = RECORDS_STU3
            all_records = view_filter(RECORDS_STU3, 'provider')
            summarized_records = []
            for record in all_records:
                if record['call_type'].lower() == "fhir":
                    # print("record processing for ", record['name'])
                    entries = get_converted_fhir_resource(fhir_data, record['resources'])
                    record['data'] = entries['entry']
                    record['count'] = len(entries['entry'])
                    summarized_records.append(record)
                elif record['call_type'].lower() == 'custom':
                    if record['name'] == 'VitalSigns':
                        entries = get_vital_signs(fhir_data, record)
                        record['data'] = entries['entry']
                        record['count'] = len(entries['entry'])
                        summarized_records.append(record)
                    elif record['name'] == 'LabResults':
                        entries = get_lab_results(fhir_data, record)
                        record['data'] = entries['entry']
                        record['count'] = len(entries['entry'])
                        summarized_records.append(record)
                else:  # skip
                    pass

            context.setdefault('return_to_view', return_to_view)
            context.setdefault('all_records', summarized_records)

        else:
            resource_profile = RECORDS_STU3[find_index(RECORDS_STU3, "slug", resource_name)]

            # print("Resource Profile", resource_profile)

            if resource_profile:
                title = resource_profile['display']
                headers = resource_profile['headers']
                exclude = resource_profile['exclude']
                # second_fields = headers
                # second_fields.append(exclude)
            else:
                title = resource_name
                headers = ['id', '*']
                exclude = ['']
                # second_fields

            title = resource_profile['display']
            if resource_profile['call_type'] == 'custom':
                if resource_profile['slug'] == 'labresults':
                    entries = get_lab_results(fhir_data, resource_profile)
                elif resource_profile['slug'] == 'vitalsigns':
                    entries = get_vital_signs(fhir_data, resource_profile)
            elif resource_profile['call_type'] == 'skip':
                entries = {'entry': []}
            else:
                entries = get_converted_fhir_resource(fhir_data, [resource_profile['name']])
                # if resource_profile['name'] == "Procedure":
                #     print(len(entries['entry']))
                #     print("Procedures:", entries['entry'])
                entries = groupsort(entries['entry'], resource_profile)
                # if resource_profile['name'] == "Procedure":
                #     print(len(entries['entry']))
                #     print("Procedures - post sort:", entries['entry'])
                entries = concatenate_lists(entry_check(entries))
                # if resource_profile['name'] == "Procedure":
                #     print(len(entries['entry']))
                #     print("Procedures - post concatenate:", entries['entry'])

            content_list = path_extract(entries['entry'], resource_profile)
            context.setdefault('friendly_fields', find_list_entry(FIELD_TITLES, "profile", resource_profile['name']))
            context.setdefault('title', title)
            context.setdefault('headers', headers)
            context.setdefault('exclude', exclude)
            # context.setdefault('content_list', content_list)
            context.setdefault('resource_profile', resource_profile)
            # sorted_content = sort_json(content_list, sort_field)
            # context.setdefault('content_list', sorted_content)
            context.setdefault('content_list', content_list)
            context.setdefault('return_to_view', return_to_view)

        return context


class ProviderDetailView(LoginRequiredMixin, SelfOrApprovedOrgMixin, TemplateView):
    template_name = "provider_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.get_member()
        data = fetch_member_data(context['member'], 'sharemyhealth')
        context['updated_at'] = parse_timestamp(data.get('updated_at'))
        context = context_updated_at(context)
        ###
        # this will only pull a local fhir file if VPC_ENV is local
        fhir_data = load_test_fhir_data(data)
        # fhir_data = data.get('fhir_data')

        if fhir_data is None or 'entry' not in fhir_data or not fhir_data['entry']:
            delete_memoized(fetch_member_data, context[
                'member'], 'sharemyhealth')

        # all_records = view_filter(RECORDS_STU3, 'provider')
        practitioner_set = get_converted_fhir_resource(fhir_data, " Practitioner")
        context['practitioner'] = practitioner_set['entry']

        if not context['practitioner']:
            raise Http404()

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
