# Generated by Django 2.1.7 on 2019-03-15 18:15

from django.db import migrations, models
import localflavor.us.models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0005_rename_resource_class_to_resource_class_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='organization',
            name='city',
            field=models.CharField(blank=True, max_length=80),
        )
    ]
