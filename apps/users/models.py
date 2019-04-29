from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Data for a user of the smh_app."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="The URL of the User's image (from VMI)"
    )

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """If the User is being created and does not have a UserProfile model, create one."""
    if created or not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()