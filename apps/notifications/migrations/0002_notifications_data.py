# Generated by Django 2.1.7 on 2019-06-24 21:48

from django.db import migrations
from django.db.models.signals import post_save

from apps.notifications.models import Notification
from apps.users.models import UserProfile, create_user_profile_connect_to_hixny_notification
from apps.org.models import ResourceRequest, create_or_update_resource_request_notifications


def notifications_up(apps, schema_editor):
    """
    Create notifications:
    * for existing members who haven't connected to Hixny
    * for existing ResourceRequests
    Use the receiver signal functions that create these notifications normally.
    """
    for user_profile in UserProfile.objects.all():
        # pretend that the UserProfile was just created in order to create the notification
        create_user_profile_connect_to_hixny_notification(UserProfile, user_profile, created=True)

    for resource_request in ResourceRequest.objects.all():
        create_or_update_resource_request_notifications(
            ResourceRequest, resource_request, created=False)


def notifications_dn(apps, schema_editor):
    """do nothing"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_notifications'),
        ('org', '0007_organization_sub'),
        ('users', '0004_auto_20190616_1737'),
    ]

    operations = [
        migrations.RunPython(notifications_up, notifications_dn),
    ]
