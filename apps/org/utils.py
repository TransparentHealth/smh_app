import base64
import io
import qrcode
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
        slug = '{}-{}'.format(slug, ''.join(
            random.choices(string.ascii_letters + string.digits, k=20)))
    instance.slug = slug


def make_qr_code(text, format='PNG', encoding='base64'):
    """
    Convert the given text to a QR-code. If encoding=='base64', return base64;
    otherwise, return raw image file data as bytes.
    """
    qr = qrcode.QRCode(version=None)
    qr.add_data(text)
    qr.make(fit=True)  # is a Pillow Image
    image = qr.make_image(fill_color="black", back_color="white")
    f = io.BytesIO()
    image.save(f, format=format)
    f.seek(0)
    b = f.read()
    if encoding == 'base64':
        return base64.b64encode(b).decode('utf-8')
    else:
        return b
