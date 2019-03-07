from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .models import Organization


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        """Add the user's Organizations to the context."""
        kwargs.setdefault('organizations', self.request.user.organization_set.all())
        return super().get_context_data(**kwargs)


class CreateOrganizationView(CreateView):
    model = Organization
    fields = ['name', 'users']
    template_name = 'organization.html'
    success_url = reverse_lazy('org:dashboard')


class UpdateOrganizationView(UpdateView):
    model = Organization
    fields = ['name', 'users']
    template_name = 'organization.html'
    success_url = reverse_lazy('org:dashboard')

    def get_queryset(self):
        """A user may only edit Organizations that they are associated with."""
        qs = super().get_queryset()
        return qs.filter(users=self.request.user)


class DeleteOrganizationView(DeleteView):
    model = Organization
    success_url = reverse_lazy('organization-list')
    template_name = 'organization_confirm_delete.html'
    success_url = reverse_lazy('org:dashboard')

    def get_queryset(self):
        """A user may only delete Organizations that they are associated with."""
        qs = super().get_queryset()
        return qs.filter(users=self.request.user)
