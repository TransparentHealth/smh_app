from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        """Add the user's Organizations to the context."""
        kwargs.setdefault('organizations', self.request.user.organization_set.all())
        return super().get_context_data(**kwargs)
