from importlib import import_module
from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField

from .utils import get_id_token_payload
from apps.data.util import parse_timestamp


class UserType:
    OTHER = ('', 'Other')
    MEMBER = ('M', 'Member')
    ORG_AGENT = ('O', 'Organization Agent')


USER_TYPE_CHOICES = (UserType.OTHER, UserType.MEMBER, UserType.ORG_AGENT)


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
        print('id_token_payload =', self.id_token_payload)
        data = {}
        data.update(**self.id_token_payload)
        data.update(
            **{
                k: (str(v) if k in ['emergency_contact_number'] else v)
                for k, v in self.__dict__.items()
                if k[0] != '_'
            }
        )
        print('UserProfile.as_dict() =', data)
        return data

    @classmethod
    def get_non_agent_profiles(cls):
        return cls.objects.select_related('user').raw(
            """
            SELECT * FROM users_userprofile WHERE id_token_payload->'organization_agent' = '[]' 
            OR id_token_payload->'organization_agent' is null
            """
        )

    @property
    def name(self):
        return ' '.join([self.user.first_name or '', self.user.last_name or '']).strip()

    @property
    def user_type(self):
        payload = self.id_token_payload
        if 'organization_agent' in payload and len(payload['organization_agent']) > 0:
            return UserType.ORG_AGENT
        return UserType.MEMBER

    @property
    def user_type_code(self):
        return self.user_type[0]

    @property
    def user_type_display(self):
        return self.user_type[1]

    @property
    def age(self):
        print('birthdate:', self.birthdate)
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


@receiver(post_save, sender=UserProfile)
def create_user_profile_connect_to_hixny_notification(
    sender, instance, created, **kwargs
):
    """Create Notifications related to the ResourceRequest, while deleting existing notifications"""
    Notification = import_module('apps.notifications.models').Notification
    if instance.user_type_code == 'O':  # Org agent
        # Delete any Hixny connection notifications for this UserProfile
        Notification.objects.filter(
            notify_id=instance.user.id,
            actor_id=instance.user.id,
            message__contains='Hixny',
        ).delete()
    elif created:
        # Create a notification to connect to Hixny
        Notification.objects.filter(
            notify_id=instance.user.id,
            actor_id=instance.user.id,
            message__contains='Hixny',
        ).delete()
        Notification.objects.create(
            notify=instance.user,
            actor=instance.user,
            instance=instance,
            message="Connect your account to <b>Hixny</b> (Health Information Exchange of New York)",
            actions=[
                {
                    'url': reverse('social:begin', args=['sharemyhealth']),
                    'method': 'get',
                    'text': "Connect Now",
                }
            ],
        )
