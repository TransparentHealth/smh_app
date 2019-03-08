from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .models import Organization, OrgResourceAccess


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        """Add the user's Organizations to the context."""
        # All of the user's Organizations
        organizations = self.request.user.organization_set.all()
        # Give each of the user's Organizations a 'org_access_to_providers' attribute
        # which is the name of each resource's provider that the Organization has
        # access to for the user. It would be faster to do this calculation with
        # an annotation using something like django.contrib.postgres.aggregates.ArrayAgg,
        # but since we are not using Postgres, we don't have that ability.
        org_provider_dict = defaultdict(list)
        for org_resource_access in OrgResourceAccess.objects.filter(user=self.request.user):
            org_provider_dict[org_resource_access.organization.id].append(
                org_resource_access.resource.provider
            )
        for organization in organizations:
            organization.org_access_to_providers = org_provider_dict[organization.id]

        kwargs.setdefault('organizations', organizations)
        return super().get_context_data(**kwargs)


class CreateOrganizationView(LoginRequiredMixin, CreateView):
    model = Organization
    fields = ['name', 'users']
    template_name = 'organization.html'
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
    template_name = 'organization.html'
    success_url = reverse_lazy('org:dashboard')

    def get_queryset(self):
        """A user may only edit Organizations that they are associated with."""
        qs = super().get_queryset()
        return qs.filter(users=self.request.user)


class DeleteOrganizationView(LoginRequiredMixin, DeleteView):
    model = Organization
    success_url = reverse_lazy('organization-list')
    template_name = 'organization_confirm_delete.html'
    success_url = reverse_lazy('org:dashboard')

    def get_queryset(self):
        """A user may only delete Organizations that they are associated with."""
        qs = super().get_queryset()
        return qs.filter(users=self.request.user)
