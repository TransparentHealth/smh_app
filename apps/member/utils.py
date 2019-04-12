from django.conf import settings
from django.shortcuts import Http404

from apps.org.models import ResourceGrant


def get_member_data(requesting_user, member, resource_name, record_type):
    """Get the data for a member from a resource."""

    # Get the path to the resource class from the settings, based on the resource_name.
    resource_class_path = settings.RESOURCE_NAME_AND_CLASS_MAPPING.get(resource_name, None)
    # If there is not a path for the resource_name, raise an error
    if not resource_class_path:
        raise Http404

    # Is the record_type is not valid, raise an error
    if record_type not in settings.VALID_MEMBER_DATA_RECORD_TYPES:
        raise Http404

    # Does the requesting_user's Organization have access to this member's resource?
    resource_grants = ResourceGrant.objects.filter(
        member=member.user,
        resource_class_path=resource_class_path,
        organization__users=requesting_user
    )
    if not resource_grants.exists():
        raise Http404
    else:
        resource_grant = resource_grants.first()

    data = resource_grant.resource_class(resource_grant.member).get(record_type)
    return data
