# Generated by Django 2.1.7 on 2019-08-23 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('users', '0004_auto_20190616_1737')]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='picture_url',
            field=models.TextField(
                blank=True,
                help_text="The URL of the User's image (from VMI)",
                null=True,
            ),
        )
    ]
