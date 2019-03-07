import random
import string

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    """An Organization."""
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        """If we're saving an Organization for the first time, give it a slug based on name."""
        if not self.id and not self.slug:
            # Create a slug from the Organization's name
            slug = slugify(self.name)
            # If this slug is already being used, create a more unique slug
            if self.__class__.objects.filter(slug=slug).exists():
                slug = '{}-{}'.format(
                    slug,
                    ''.join(random.choices(string.ascii_letters + string.digits, k=20))
                )
            self.slug = slug

        super().save(**kwargs)
