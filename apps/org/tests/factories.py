import random

from django.conf import settings
from django.template.defaultfilters import slugify
from factory import DjangoModelFactory, Faker, LazyAttribute, SubFactory

from ..models import Organization, ResourceGrant


class OrganizationFactory(DjangoModelFactory):
    slug = LazyAttribute(lambda o: slugify(o.name))
    name = Faker('company')
    phone = Faker('phone_number')
    street_line_1 = Faker('street_address')
    street_line_2 = 'Room {}'.format(random.randint(0, 1000))
    city = Faker('city')
    state = Faker('state_abbr')
    zipcode = Faker('zipcode')

    class Meta:
        model = Organization


class UserFactory(DjangoModelFactory):
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Faker('email')
    username = Faker('user_name')

    class Meta:
        model = settings.AUTH_USER_MODEL


class UserSocialAuthFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)

    class Meta:
        model = 'social_django.UserSocialAuth'


class ResourceGrantFactory(DjangoModelFactory):
    organization = SubFactory(OrganizationFactory)
    user = SubFactory(UserFactory)

    class Meta:
        model = ResourceGrant
