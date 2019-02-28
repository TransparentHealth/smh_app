from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse


@login_required(login_url='home')
def resources_page(request):
    """Render a page of resources."""
    resource_provider_names = [getattr(settings, 'SOCIAL_AUTH_SHAREMYHEALTH_NAME')]
    resources_for_user = request.user.social_auth.filter(provider__in=resource_provider_names)

    current_resources = [
        {
            'name': resource.provider,
            'url': reverse('social:begin', kwargs={'backend': resource.provider})
        }
        for resource in resources_for_user
    ]
    return render(request, 'resources.html', context={'resources': current_resources})
