# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import user_router


# Copyright Videntity Systems Inc.

app_name = 'users'
urlpatterns = [
    url(r'^router/$',
        user_router,
        name='user_router'),
]
