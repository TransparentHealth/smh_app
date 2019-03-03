# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import organization_dashboard


# Copyright Videntity Systems Inc.

urlpatterns = [
    url(r'^dashboard$',
        organization_dashboard, name='organization_dashboard'),

]
