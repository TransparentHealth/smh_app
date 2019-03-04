# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import DashboardView


# Copyright Videntity Systems Inc.

app_name = 'org'
urlpatterns = [
    url(r'^dashboard$',
        DashboardView.as_view(), name='dashboard'),

]
