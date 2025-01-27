# Generated by Django 2.1.7 on 2019-06-24 21:48

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [('contenttypes', '0002_remove_content_type_name')]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('notify_id', models.PositiveIntegerField()),
                ('actor_id', models.PositiveIntegerField()),
                ('target_id', models.PositiveIntegerField(null=True)),
                ('instance_id', models.PositiveIntegerField(null=True)),
                ('message', models.TextField()),
                ('picture_url', models.TextField(null=True)),
                (
                    'actions',
                    django.contrib.postgres.fields.jsonb.JSONField(default=list),
                ),
                ('dismissed', models.BooleanField(default=False)),
                (
                    'actor_content_type',
                    models.ForeignKey(
                        choices=[(4, 'auth.user'), (7, 'org.organization')],
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='contenttypes.ContentType',
                    ),
                ),
                (
                    'instance_content_type',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='contenttypes.ContentType',
                    ),
                ),
                (
                    'notify_content_type',
                    models.ForeignKey(
                        choices=[(4, 'auth.user'), (7, 'org.organization')],
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='contenttypes.ContentType',
                    ),
                ),
                (
                    'target_content_type',
                    models.ForeignKey(
                        choices=[(4, 'auth.user'), (7, 'org.organization')],
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='contenttypes.ContentType',
                    ),
                ),
            ],
            options={'abstract': False},
        )
    ]
