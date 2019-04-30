# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import UserSettingsView


# Copyright Videntity Systems Inc.

app_name = 'users'
urlpatterns = [
    url(r'^settings$',
        UserSettingsView.as_view(),
        name='user_settings'),
]
