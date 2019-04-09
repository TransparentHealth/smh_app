from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True, unique=False)
    address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(null=True, blank=True, max_length=40)
    emergency_contact_number = PhoneNumberField(null=True, blank=True, unique=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
        If the User is being created or does not have a related Member model, create one.
        Otherwise update existing member
    """
    if created or not hasattr(instance, 'member'):
        Member.objects.create(user=instance)
    instance.member.save()
