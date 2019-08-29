import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from getenv import env

logger = logging.getLogger('smhapp.%s' % __name__)


def create_superuser(username, password, email):
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        # Otherwise we instantiate the super user
        u = User(username=username, first_name="Super", last_name="User", email=email)
    u.set_password(password)
    u.is_superuser = True
    u.is_staff = True
    u.save()
    return True


class Command(BaseCommand):
    help = 'Create a super user from environment variables ROOT_USER ROOT_PASSWORD and ROOT_EMAIL'

    def handle(self, *args, **options):

        # get variables
        super_username = env("ROOT_USER", "")
        super_password = env("ROOT_PASSWORD", "")
        super_email = env("ROOT_EMAIL", "%s@locahost.com" % (super_username))
        if super_username and super_password and super_email:
            # create a super user
            r = create_superuser(super_username, super_password, super_email)
            if r:
                logger.info('Superuser created/updated.')
            else:
                logger.info('Something went wrong creating/updating superuser')
        else:
            logger.debug(
                'Environment variables ROOT_USER, ROOT_PASSWORD,',
                'ROOT_EMAIL must be set before using this command.',
            )
