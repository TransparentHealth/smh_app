from importlib import import_module

from django.conf import settings
from django.db import models

from .utils import set_unique_slug


RESOURCE_CHOICES = [
    ('apps.sharemyhealth.resources.Resource', 'apps.sharemyhealth.resources.Resource')
]


class Organization(models.Model):
    """An Organization."""
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def set_unique_slug(self):
        """Call the set_unique_slug() utility function to give the instance a unique slug."""
        set_unique_slug(self, based_on_field='name')

    def save(self, **kwargs):
        """If we're saving an Organization for the first time, give it a slug based on name."""
        if not self.id and not self.slug:
            self.set_unique_slug()

        super().save(**kwargs)


class ResourceGrant(models.Model):
    """A model to track which Organizations have access to which users' resources."""
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    resource_class = models.CharField(
        max_length=255,
        choices=RESOURCE_CHOICES,
        default=RESOURCE_CHOICES[0][0]
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} access to {} for {}".format(self.organization, self.provider_name, self.user)

    @property
    def provider_name(self):
        """Return the 'name' of the resource_class."""
        # First, import the class
        resource_module = '.'.join(self.resource_class.split('.')[:-1])
        resource_class_name = self.resource_class.split('.')[-1]
        resource_class = getattr(import_module(resource_module), resource_class_name)
        # Return the class' name
        return resource_class.name

    class Meta:
        verbose_name_plural = "Resource Grants"
