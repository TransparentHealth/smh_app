# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import member_dashboard

# Copyright Videntity Systems Inc.

urlpatterns = [
    url(r'^(?P<subject>[^/]+)$',
        member_dashboard, name='member_dashboard_subject'),

    url(r'^$',
        member_dashboard, name='member_dashboard'),

]
