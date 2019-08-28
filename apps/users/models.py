from collections import OrderedDict
from datetime import date
from enum import Enum
from importlib import import_module

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField

from apps.data.util import parse_timestamp


class UserType(Enum):
    OTHER = ''
    MEMBER = 'M'
    ORG_AGENT = 'O'


USER_TYPE_CHOICES = OrderedDict(
    (
        (UserType.OTHER.value, 'Other'),
        (UserType.MEMBER.value, 'Member'),
        (UserType.ORG_AGENT.value, "Organization Agent"),
    )
)


# Make user_type a property of the User model, because that is where it is tested
def user_type(self):
    if self.agent_organizations.exists():
        return UserType.ORG_AGENT.value
    elif self.member_organizations.exists():
        return UserType.MEMBER.value
    else:
        return UserType.OTHER.value


User.user_type = property(user_type)


class UserProfile(models.Model):
    """Data for a user of the smh_app."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Holds the payload value of the VMI socialauth id_token
    id_token_payload = JSONField(default=dict, encoder=DjangoJSONEncoder)

    # Most of the UserProfile data is stored in the VMI socialauth id_token, but these are not
    emergency_contact_name = models.CharField(null=True, blank=True, max_length=128)
    emergency_contact_number = PhoneNumberField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def __getattr__(self, key):
        """Provide direct read access to attributes of the id_token."""
        # self.__getattribute__(key) failed, so check self.id_token_payload
        return self.id_token_payload.get(key)

    def as_dict(self):
        """return the UserProfile object as a json-able dict"""
        data = dict(**self.id_token_payload)
        data.update(
            **{
                k: (str(v) if k in ['emergency_contact_number'] else v)
                for k, v in self.__dict__.items()
                if k[0] != '_'
            }
        )
        return data

    @property
    def name(self):
        return ' '.join([self.user.first_name or '', self.user.last_name or '']).strip()

    @property
    def age(self):
        try:
            born = parse_timestamp(self.birthdate).date()
            today = date.today()
            age = today.year - born.year
            if age < 0:
                return "Unknown"
            else:
                return age
        except Exception:
            return "Unknown"

    @property
    def subject(self):
        return self.id_token_payload.get('sub')


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """If the User is being created and does not have a UserProfile model, create one."""
    if created or not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()


# This is still tied to UserProfile (rather than User) for historical migration reasons.
@receiver(post_save, sender=UserProfile)
def create_user_profile_connect_to_hixny_notification(
    sender, instance, created, **kwargs
):
    """Create Notifications related to the ResourceRequest, 
        while deleting existing notifications
    """
    Notification = import_module('apps.notifications.models').Notification
    user = instance.user
    if user.user_type == 'O':  # Org agent
        # Delete any Hixny connection notifications for this UserProfile
        Notification.objects.filter(
            notify_id=user.id, actor_id=user.id, message__contains='Hixny'
        ).delete()
    elif created:
        # Create a notification to connect to Hixny
        Notification.objects.filter(
            notify_id=user.id, actor_id=user.id, message__contains='Hixny'
        ).delete()
        Notification.objects.create(
            notify=user,
            actor=user,
            instance=user,
            message="Connect your account to <b>Hixny</b> (Health Information Exchange of New York)",
            actions=[
                {
                    'url': reverse('social:begin', args=['sharemyhealth']),
                    'method': 'get',
                    'text': "Connect Now",
                }
            ],
        )
