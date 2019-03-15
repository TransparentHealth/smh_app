from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"



class DataSourcesView(LoginRequiredMixin, TemplateView):
    template_name = "data_sources.html"
