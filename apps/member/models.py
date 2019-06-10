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
    birth_date = models.DateField(null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True, unique=False)
    address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(
        null=True, blank=True, max_length=40)
    emergency_contact_number = PhoneNumberField(
        null=True, blank=True, unique=False)
    organizations = models.ManyToManyField(
        Organization, blank=True, related_name='members')

    def __str__(self):
        return self.user.username

    def parsed_id_token(self):
        return get_id_token_payload(self.user)

    def age(self):
        idt = get_id_token_payload(self.user)
        bd = idt['birthdate']
        born = datetime.strptime(bd, '%Y-%m-%d').date()
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
        If the User is being created or does not have a related Member model, create one.
        Otherwise update existing member
    """
    if created or not hasattr(instance, 'member'):
        Member.objects.create(user=instance)
    instance.member.save()
