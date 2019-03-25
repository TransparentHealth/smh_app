from importlib import import_module

from django.conf import settings
from django.db import models

from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField

from .utils import set_unique_slug
from ..common.models import CreatedUpdatedModel


RESOURCE_CHOICES = [
    ('apps.sharemyhealth.resources.Resource', 'apps.sharemyhealth.resources.Resource')
]
REQUEST_REQUESTED = 'Requested'
REQUEST_APPROVED = 'Approved'
REQUEST_DENIED = 'Denied'
RESOURCE_REQUEST_STATUSES = [
    (REQUEST_REQUESTED, REQUEST_REQUESTED),
    (REQUEST_APPROVED, REQUEST_APPROVED),
    (REQUEST_DENIED, REQUEST_DENIED),
]


class Organization(CreatedUpdatedModel, models.Model):
    """An Organization."""
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    phone = PhoneNumberField(blank=True)
    street_line_1 = models.CharField(max_length=255, blank=True)
    street_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = USStateField(blank=True)
    zipcode = USZipCodeField(blank=True)

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


class ResourceGrant(CreatedUpdatedModel, models.Model):
    """A model to track which Organizations have access to which users' resources."""
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text='The member who has granted this Organization access to the resource'
    )
    resource_class_path = models.CharField(
        max_length=255,
        choices=RESOURCE_CHOICES,
        default=RESOURCE_CHOICES[0][0]
    )
    resource_request = models.OneToOneField(
        'org.ResourceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return "{} access to {} for {}".format(self.organization, self.provider_name, self.member)

    @property
    def provider_name(self):
        """Return the 'name' of the resource_class."""
        # First, import the class
        resource_module = '.'.join(self.resource_class_path.split('.')[:-1])
        resource_class_name = self.resource_class_path.split('.')[-1]
        resource_class = getattr(import_module(resource_module), resource_class_name)
        # Return the class' name
        return resource_class.name

    class Meta:
        verbose_name_plural = "Resource Grants"


class ResourceRequest(CreatedUpdatedModel, models.Model):
    """A request from an Organization for access to a member's access token."""
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_requests_received',
        help_text='The member who can grant this Organization access to the resource'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_requests_sent',
        help_text='The user at the Organization who initiated this request'
    )
    resource_class_path = models.CharField(
        max_length=255,
        choices=RESOURCE_CHOICES,
        default=RESOURCE_CHOICES[0][0]
    )
    status = models.CharField(
        max_length=10,
        choices=RESOURCE_REQUEST_STATUSES,
        default=REQUEST_REQUESTED
    )

    def __str__(self):
        return "Request by {} for access to {} for {}".format(
            self.organization,
            self.provider_name,
            self.member
        )

    @property
    def provider_name(self):
        """Return the 'name' of the resource_class."""
        # First, import the class
        resource_module = '.'.join(self.resource_class_path.split('.')[:-1])
        resource_class_name = self.resource_class_path.split('.')[-1]
        resource_class = getattr(import_module(resource_module), resource_class_name)
        # Return the class' name
        return resource_class.name

    class Meta:
        verbose_name_plural = "Resource Requests"
