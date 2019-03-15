from django.db import models


class CreatedUpdatedModel(models.Model):
    """An abstract model with fields to keep track of when an object is created and updated."""
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
