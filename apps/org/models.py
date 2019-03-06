from django.conf import settings
from django.db import models


class Organization(models.Model):
    """An Organization."""
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    def __str__(self):
        return self.name
