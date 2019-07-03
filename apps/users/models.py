from importlib import import_module
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from ..member.utils import get_id_token_payload

class UserProfile(models.Model):
    """Data for a user of the smh_app."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subject = models.CharField(
        max_length=64, blank=True, null=True, help_text='Subject for identity token', db_index=True)
    picture_url = models.TextField(blank=True, help_text="The URL of the User's image (from VMI)")
    user_type = models.CharField(
        max_length=255,
        blank=True,
        choices=(('', 'Other'), ('M', 'Member'), ('O', 'Organization Agent')),
        default="M",
        help_text="What kind of user is this? This controls what dashboard the user sees.",
    )

    def __str__(self):
        return self.user.username

    @property
    def name(self):
        return ' '.join([self.user.first_name or '', self.user.last_name or '']).strip()
    
    @property
    def id_token_payload(self):
        return get_id_token_payload(self.user)


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
    if instance.user_type == 'O':
        # Delete any Hixny connection notifications for this UserProfile
        Notification.objects.filter(
            notify_id=instance.user.id, actor_id=instance.user.id,
            message__contains='Hixny').delete()
    elif created:
        # Create a notification to connect to Hixny
        Notification.objects.filter(
            notify_id=instance.user.id, actor_id=instance.user.id,
            message__contains='Hixny').delete()
        Notification.objects.create(
            notify=instance.user,
            actor=instance.user,
            instance=instance,
            message="Connect your account to <b>Hixny</b> (Health Information Exchange of New York)",
            actions=[{
                'url': reverse('social:begin', args=['sharemyhealth']),
                'method': 'get',
                'text': "Connect Now"
            }],
        )
