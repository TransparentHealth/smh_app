# Generated by Django 2.1.11 on 2019-12-08 17:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0010_update_resources'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='users',
        ),
    ]
