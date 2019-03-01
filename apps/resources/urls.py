from django.urls import include, path

from .views import resources_page

urlpatterns = [
    path('', resources_page, name='resources'),
]
