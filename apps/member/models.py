from django.db import models
from django.contrib.auth.models import User
from apps.users.utils import get_id_token_payload
from apps.org.models import Organization

"""
The Member model is DEPRECATED -- retained until we're sure all data successfully migrates.

* User profile data is migrated to apps.users.models.UserProfile
* Organization membership relationships are migrated to Organization.members
  (which points to User, which has related_name User.member_organizations)
"""

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # organizations field DEPRECATED: use Organization.members field instead
    organizations = models.ManyToManyField(
        Organization, blank=True, related_name='members_organizations')

    def __str__(self):
        return self.user.username

    def parsed_id_token(self):
        return get_id_token_payload(self.user)

