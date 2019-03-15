# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import DashboardView, DataSourcesView

# Copyright Videntity Systems Inc.

app_name = 'member'
urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^$', DataSourcesView.as_view(), name='data_sources'),
]
