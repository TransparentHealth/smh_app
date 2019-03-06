from django.template.defaultfilters import slugify
from factory import DjangoModelFactory, Faker, LazyAttribute

from ..models import Organization


class OrganizationFactory(DjangoModelFactory):
    slug = LazyAttribute(lambda o: slugify(o.name))
    name = Faker('company')

    class Meta:
        model = Organization
