# Copyright Videntity Systems, Inc.
from django.conf.urls import url
from .views import RecordsView, DataSourcesView, CreateMemberView, UpdateMemberView, DeleteMemberView

# Copyright Videntity Systems Inc.

app_name = 'member'
urlpatterns = [
    url(r'^(?P<pk>\d)/records/$',
        RecordsView.as_view(),
        name='records'),
    url(r'^(?P<pk>\d)/data-sources/$',
        DataSourcesView.as_view(),
        name='data-sources'),
    url(r'^new/$',
        CreateMemberView.as_view(),
        name='member-create'),
    url(r'^(?P<pk>\d)/$',
        UpdateMemberView.as_view(),
        name='member-update'),
    url(r'^(?P<pk>\d)/delete/$',
        DeleteMemberView.as_view(),
        name='member-delete'),
]
