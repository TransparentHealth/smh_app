from django.conf import settings
from django.template.defaultfilters import slugify
from factory import DjangoModelFactory, Faker, LazyAttribute

from ..models import Organization


class OrganizationFactory(DjangoModelFactory):
    slug = LazyAttribute(lambda o: slugify(o.name))
    name = Faker('company')

    class Meta:
        model = Organization


class UserFactory(DjangoModelFactory):
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Faker('email')
    username = Faker('user_name')

    class Meta:
        model = settings.AUTH_USER_MODEL
