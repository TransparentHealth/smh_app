from django.conf import settings
from django.db import models

from .utils import set_unique_slug


class Organization(models.Model):
    """An Organization."""
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

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
