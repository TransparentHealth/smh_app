# Generated by Django 2.1.7 on 2019-05-02 12:33

import os
from django.db import migrations


class Migration(migrations.Migration):

    def create_root_user(apps, schema_editor):
        if not os.getenv("ROOT_USER", False) or not os.getenv("ROOT_PASSWORD", False):
            raise Exception("Misconfigured, initial root user name and password should be in the env")
        from django.contrib.auth.models import User
        User.objects.create_superuser(os.getenv("ROOT_USER"), os.getenv("ROOT_USER"), os.getenv("ROOT_PASSWORD"))

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_root_user),
    ]