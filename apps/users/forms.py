from django.forms import Form, ImageField


class UserSettingsForm(Form):
    """A form for a User to update their settings."""
    picture = ImageField(required=True)
