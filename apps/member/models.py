from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import get_id_token_payload
from apps.org.models import Organization
from datetime import date, datetime


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # organizations field DEPRECATED: use Organization.members field instead
    organizations = models.ManyToManyField(
        Organization, blank=True, related_name='members_organizations')

    def __str__(self):
        return self.user.username

    def parsed_id_token(self):
        return get_id_token_payload(self.user)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
        If the User is being created or does not have a related Member model, create one.
        Otherwise update existing member
    """
    if created or not hasattr(instance, 'member'):
        Member.objects.create(user=instance)
    instance.member.save()
