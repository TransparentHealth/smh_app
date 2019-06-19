from apps.org.models import ResourceRequest
from apps.member.models import Member

def resource_requests(request):
    if not request.user.is_anonymous:
        resource_requests = ResourceRequest.objects.filter(member=request.user).order_by('-updated')[:8]
    else:
        resource_requests = ResourceRequest.objects.none()
    return {
        'resource_requests': resource_requests,
    }