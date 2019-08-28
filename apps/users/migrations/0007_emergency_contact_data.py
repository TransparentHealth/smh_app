# Generated by Django 2.1.7 on 2019-08-23 23:29

from importlib import import_module

from django.db import migrations


def forward(apps, schema_editor):
    db = schema_editor.connection.alias
    UserProfile = apps.get_model('users', 'UserProfile')
    for profile in UserProfile.objects.all().select_related('user__member'):
        if hasattr(profile.user, 'member'):
            profile.emergency_contact_name = profile.user.member.emergency_contact_name
            profile.emergency_contact_number = (
                profile.user.member.emergency_contact_number
            )
            profile.save()


def reverse(apps, schema_editor):
    db = schema_editor.connection.alias
    UserProfile = apps.get_model('users', 'UserProfile')
    for profile in UserProfile.objects.all().select_related('user__member'):
        if hasattr(profile.user, 'member'):
            profile.user.member.emergency_contact_name = profile.emergency_contact_name
            profile.user.member.emergency_contact_number = (
                profile.emergency_contact_number
            )
            profile.user.member.save()


class Migration(migrations.Migration):

    dependencies = [('users', '0006_update_userprofile')]

    operations = [migrations.RunPython(forward, reverse)]
