from django.db import models


class CreatedModel(models.Model):
    """An abstract model with a field to keep track of when an object is created."""

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class CreatedUpdatedModel(CreatedModel, models.Model):
    """An abstract model with fields to keep track of when an object is created and updated."""

    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
