# Copyright Videntity Systems, Inc.
from django.conf.urls import url

from .views import DismissNotificationView

app_name = 'notifications'
urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/dismiss/$', DismissNotificationView.as_view(), name='dismiss')
]
