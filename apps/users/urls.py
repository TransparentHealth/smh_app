# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import UserSettingsView, user_member_router


# Copyright Videntity Systems Inc.

app_name = 'users'
urlpatterns = [
    url(r'^user_member_router/$',
        user_member_router,
        name='user_member_router'),
    url(r'^settings$',
        UserSettingsView.as_view(),
        name='user_settings'),
]
