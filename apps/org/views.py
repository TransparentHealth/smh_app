from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.models import User
from django.views import View
from django.http import JsonResponse

import requests

from .models import Organization
from apps.member.models import Member
from smh_app.utils import get_vmi_user_data


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "org/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add the user's Organization and members of that organization to the context."""
        org = self.request.user.organization_set.all()
        members = User.objects.all() if org is not None else None
        kwargs.setdefault('organization', org)
        kwargs.setdefault('members', members)
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


class LocalUserAPI(LoginRequiredMixin, View):
    ''' Setting up a local endpoint that talks to the VMI endpoint and filters to
        only include users with user social auth uids that match '''
    def get(self, request, *args, **kwargs):
        response = get_vmi_user_data(request)
        user_data = []

        if isinstance(response.json(), list):
            for i, user in enumerate(response.json(), 0):
                # we only choose users/members with valid user social auth uids that match a field from VMI called 'sub'
                member = User.social_auth.rel.related_model.objects.filter(uid=user['sub']).first()
                if member:
                    # add id so we can use in template (main.js)
                    user['id'] = member.user.id
                    user_data.append(user)

        return JsonResponse(user_data, safe=False)


class SearchView(LoginRequiredMixin, TemplateView):
    """template view that mostly uses javascript to render content"""
    template_name = "org/search.html"
