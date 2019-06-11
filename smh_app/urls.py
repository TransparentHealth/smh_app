"""smh_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import TemplateView
from django.urls import include, path
from django.contrib.auth import views as auth_views


urlpatterns = [
    path(
        '',
        TemplateView.as_view(
            template_name='homepage.html',
            extra_context={'SOCIAL_AUTH_NAME': settings.SOCIAL_AUTH_NAME}
        ),
        name='home'
    ),
    path('logout/', auth_views.LogoutView.as_view(),
         {'next_page': '/'}, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path(r'resources/', include('apps.resources.urls')),
    path(r'org/', include('apps.org.urls')),
    path(r'member/', include('apps.member.urls')),
    path(r'user/', include('apps.users.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
]
