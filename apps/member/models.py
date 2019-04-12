from django.contrib.auth.models import User


class Member(User):
    class Meta:
        proxy = True
