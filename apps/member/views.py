from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView

import requests

from .models import Member
from .constants import RECORDS


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
    fields = ['user', 'birth_date', 'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_number' ]
    template_name = 'member.html'
    # success_url = reverse_lazy('org:dashboard')
    def get_success_url(self):
        member_id = self.object.id
        return reverse_lazy( 'member:member-update', kwargs={'pk': member_id})


class UpdateMemberView(LoginRequiredMixin, UpdateView):
    model = Member
    fields = ['birth_date', 'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_number' ]
    template_name = 'member.html'

    def get_success_url(self):
        member_id = self.object.id
        return reverse_lazy( 'member:member-update', kwargs={'pk': member_id})


class DeleteMemberView(LoginRequiredMixin, DeleteView):
    model = Member
    template_name = 'member_confirm_delete.html'
    success_url = reverse_lazy('org:dashboard')
