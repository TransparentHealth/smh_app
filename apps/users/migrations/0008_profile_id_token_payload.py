# Generated by Django 2.1.11 on 2019-08-27 13:54

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations
from jwkest.jwt import JWT


def forward(apps, schema_editor):
    """Copy existing VMI social auth id_token payloads into the new UserProfile.id_token_payload field"""
    db = schema_editor.connection.alias
    UserProfile = apps.get_model('users', 'UserProfile')
    for profile in UserProfile.objects.using(db).all():
        vmi = profile.user.social_auth.filter(provider='vmi').first()
        if vmi:
            id_token = vmi.extra_data.get('id_token')
            profile.id_token_payload = JWT().unpack(id_token).payload()
            profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_emergency_contact_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='id_token_payload',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.RunPython(forward, lambda: None)
    ]
