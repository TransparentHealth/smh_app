# Generated by Django 2.1.7 on 2019-05-31 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('users', '0002_auto_20190502_1233')]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='subject',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Subject for identity token',
                max_length=64,
                null=True,
            ),
        )
    ]
