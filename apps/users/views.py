from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from .forms import UserSettingsForm


class UserSettingsView(LoginRequiredMixin, FormView):
    """A view for allowing a User to change their user settings."""
    template_name = 'users/user_settings.html'
    form_class = UserSettingsForm
    login_url = 'home'
    # If there are any non-form errors, they can be stored in self.errors, and
    # will be displayed in the template.
    errors = {}

    def get_context_data(self, **kwargs):
        """Get the context data for the template."""
        kwargs.setdefault('errors', self.errors)
        return super().get_context_data(**kwargs)
