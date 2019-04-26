from django.contrib.auth.models import User

from apps.org.models import Organization


class Member(User):
    class Meta:
        proxy = True
