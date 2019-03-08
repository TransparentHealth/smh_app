import random
import string

from django.utils.text import slugify


def set_unique_slug(instance, based_on_field='name'):
    """
    Give this instance a unique slug:

      - First, try to use Django's slugify() function to come up with a unique slug
        based on the based_on_field.
      - Second, if the slug is not unique, then give the slug a random string at
        the end.
    """
    # Create a slug from the Organization's name
    slug = slugify(getattr(instance, based_on_field))
    # If this slug is already being used, create a more unique slug
    if instance.__class__.objects.filter(slug=slug).exists():
        slug = '{}-{}'.format(
            slug,
            ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        )
    instance.slug = slug
