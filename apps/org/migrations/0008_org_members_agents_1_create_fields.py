# Generated by Django 2.1.11 on 2019-08-26 20:00

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('org', '0007_organization_sub'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='agents',
            field=models.ManyToManyField(
                blank=True,
                related_name='agent_organizations',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='members',
            field=models.ManyToManyField(
                blank=True,
                related_name='member_organizations',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='organization',
            name='users',
            field=models.ManyToManyField(
                blank=True,
                related_name='organizations',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Agents',
            ),
        ),
    ]
