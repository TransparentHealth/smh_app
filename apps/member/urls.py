# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import DashboardView, approve_resource_request

# Copyright Videntity Systems Inc.

app_name = 'member'
urlpatterns = [
    url(r'^$',
        DashboardView.as_view(), name='dashboard'),
    url(r'^approve_resource_request/(?P<pk>[0-9]+)/$',
        approve_resource_request,
        name='approve_resource_request'),
]
