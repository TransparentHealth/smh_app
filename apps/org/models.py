from importlib import import_module

from django.conf import settings
from django.db import models
from django.utils.html import mark_safe
from django.utils.timezone import now
# from django.contrib.humanize import naturaltime


from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField

from .utils import set_unique_slug
from .tokens import default_token_generator
from ..common.models import CreatedUpdatedModel


RESOURCE_CHOICES = [
    (value, value) for value in settings.RESOURCE_NAME_AND_CLASS_MAPPING.values()
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

    @property
    def invite_token(self):
        return default_token_generator.make_token(self)


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
        return self.resource_class.name

    @property
    def resource_class(self):
        """Return the class that the resource_class_path refers to."""
        resource_module = '.'.join(self.resource_class_path.split('.')[:-1])
        resource_class_name = self.resource_class_path.split('.')[-1]
        return getattr(import_module(resource_module), resource_class_name)

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
        return self.resource_class.name

    @property
    def resource_class(self):
        """Return the class that the resource_class_path refers to."""
        resource_module = '.'.join(self.resource_class_path.split('.')[:-1])
        resource_class_name = self.resource_class_path.split('.')[-1]
        return getattr(import_module(resource_module), resource_class_name)

    @property
    def notification_text(self):
        if self.status == REQUEST_REQUESTED:
            return mark_safe("<b>{}</b> requested access to your data".format(self.organization))
        elif self.status == REQUEST_APPROVED:
            return mark_safe("You allowed <b>{}</b> to access your data".format(self.organization))
        elif self.status == REQUEST_DENIED:
            return mark_safe("You revoked access to <b>{}</b> to your data".format(self.organization))

    @property
    def actions(self):
        if self.status == REQUEST_REQUESTED:
            return [
                {'url': 'member:revoke_resource_request', 'button_text': 'Dismiss' },
                {'url': 'member:approve_resource_request', 'button_text': 'Accept Request' },
            ]
        elif self.status == REQUEST_APPROVED:
            return [{'url': 'member:revoke_resource_request', 'button_text': 'Revoke' }]
        elif self.status == REQUEST_DENIED:
            return [{'url': 'member:approve_resource_request', 'button_text': 'Re-Approve Access' }]



    class Meta:
        verbose_name_plural = "Resource Requests"
