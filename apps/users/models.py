from importlib import import_module
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField

from ..member.utils import get_id_token_payload


class UserType:
    OTHER = ('', 'Other')
    MEMBER = ('M', 'Member')
    ORG_AGENT = ('O', 'Organization Agent')


USER_TYPE_CHOICES = (UserType.OTHER, UserType.MEMBER, UserType.ORG_AGENT)


class UserProfile(models.Model):
    """Data for a user of the smh_app."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Most of the UserProfile data is stored in the VMI socialauth id_token, but these are not
    emergency_contact_name = models.CharField(null=True, blank=True, max_length=128)
    emergency_contact_number = PhoneNumberField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def __getattr__(self, key):
        """Provide direct read access to attributes of the id_token."""
        # self.__getattribute__(key) failed, so check self.id_token_payload
        return self.id_token_payload.get(key)

    @property
    def id_token_payload(self):
        return get_id_token_payload(self.user)

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
    def age(self):
        try:
            idt = self.id_token_payload()
            bd = idt['birthdate']
            born = datetime.strptime(bd, '%Y-%m-%d').date()
            today = date.today()
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        except Exception:
            return "Unknown"



@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """If the User is being created and does not have a UserProfile model, create one."""
    if created or not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()


@receiver(post_save, sender=UserProfile)
def create_user_profile_connect_to_hixny_notification(sender, instance, created, **kwargs):
    """Create Notifications related to the ResourceRequest, while deleting existing notifications"""
    Notification = import_module('apps.notifications.models').Notification
    if instance.user_type == 'O':  # Org agent
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
            actions=[{
                'url': reverse('social:begin', args=['sharemyhealth']),
                'method': 'get',
                'text': "Connect Now",
            }],
        )
