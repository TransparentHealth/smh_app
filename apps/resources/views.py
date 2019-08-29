from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse


@login_required(login_url='home')
def resources_page(request):
    """Render a page of resources."""
    # A list of resources that may show up on the page
    resource_provider_names = ['sharemyhealth']
    # The resources that the user is currently connected to
    connected_resource_names = request.user.social_auth.filter(
        provider__in=resource_provider_names
    ).values_list('provider', flat=True)
    # All of the user's resources, whether they are connected or not
    resources = [
        {
            'name': resource_name,
            'connected': resource_name in connected_resource_names,
            'connect_url': reverse('social:begin', kwargs={'backend': resource_name}),
            'disconnect_url': reverse(
                'social:disconnect', kwargs={'backend': resource_name}
            ),
        }
        for resource_name in resource_provider_names
    ]
    return render(request, 'resources/resources.html', context={'resources': resources})
