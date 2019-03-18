from django.conf import settings

from factory import DjangoModelFactory, Faker


class UserFactory(DjangoModelFactory):
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Faker('email')
    username = Faker('user_name')

    class Meta:
        model = settings.AUTH_USER_MODEL
