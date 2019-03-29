from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, Http404, render, redirect, reverse
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView

from apps.org.models import (
    ResourceGrant, ResourceRequest, REQUEST_APPROVED, REQUEST_DENIED, REQUEST_REQUESTED
)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "member/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add ResourceRequests for the user's resources to the context."""
        # Get all of the ResourceRequests for access to the self.request.user's resources
        resource_requests = ResourceRequest.objects.filter(
            member=self.request.user
        ).filter(
            status=REQUEST_REQUESTED
        )
        resources_granted = ResourceRequest.objects.filter(
            member=self.request.user
        ).filter(
            status=REQUEST_APPROVED
        )
        kwargs.setdefault('resource_requests', resource_requests)
        kwargs.setdefault('resources_granted', resources_granted)
        return super().get_context_data(**kwargs)


@require_POST
@login_required(login_url='home')
def approve_resource_request(request, pk):
    """
    A view for a member to approve a ResourceRequest.

    Approving a ResourceRequest means settings its status to 'Approved', and
    creating a ResourceGrant.
    """
    # Is the ResourceRequest for this member?
    resource_request = get_object_or_404(
        ResourceRequest.objects.filter(member=request.user),
        pk=pk
    )
    resource_request.status = REQUEST_APPROVED
    resource_request.save()
    # The ResourceRequest is for this member, so create a ResourceGrant for it
    ResourceGrant.objects.create(
        organization=resource_request.organization,
        member=resource_request.member,
        resource_class_path=resource_request.resource_class_path,
        resource_request=resource_request
    )
    return redirect(reverse('member:dashboard'))


@require_POST
@login_required(login_url='home')
def revoke_resource_request(request, pk):
    """
    A view for a member to revoke access to a resource (after an approved ResourceRequest).

    Revoking a ResourceRequest means settings its status to 'Denied', and
    deleting the related ResourceGrant.
    """
    # Is the ResourceRequest for this member?
    resource_request = get_object_or_404(
        ResourceRequest.objects.filter(member=request.user),
        pk=pk
    )
    # The ResourceRequest is for this member; set its status to REQUEST_DENIED.
    resource_request.status = REQUEST_DENIED
    resource_request.save()
    # The ResourceRequest is for this member, so delete the relevant ResourceGrant
    if getattr(resource_request, 'resourcegrant', None):
        resource_request.resourcegrant.delete()
    return redirect(reverse('member:dashboard'))


@login_required(login_url='home')
def get_member_data(request, pk, resource_name, record_type):
    # Get the path to the resource class from the settings, based on the resource_name.
    resource_class_path = settings.RESOURCE_NAME_AND_CLASS_MAPPING.get(resource_name, None)
    # If there is not a path for the resource_name, raise an error
    if not resource_class_path:
        raise Http404

    # Is the record_type is not valid, raise an error
    if record_type not in settings.VALID_MEMBER_DATA_RECORD_TYPES:
        raise Http404

    # Does the request.user's Organization have access to this member's resource?
    resource_grant = get_object_or_404(
        ResourceGrant.objects.filter(
            member_id=pk,
            resource_class_path=resource_class_path,
            organization__users=request.user
        )
    )

    data = resource_grant.resource_class(resource_grant.member).get(record_type)
    return render(request, 'member/data.html', context={'data': data})
