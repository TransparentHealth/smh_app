from django.forms import CharField, ChoiceField, DateField, EmailField, Form


# Choices for a user's gender field in VMI
GENDER_CHOICES = (
    ('', 'Unspecified'),
    ('female', 'Female'),
    ('male', 'Male'),
)


class CreateNewMemberAtOrgForm(Form):
    """
    A form creating a new Member at an Organization.

    This form is used in the first step of the process for an Organization user
    to help a person become a Member at that Organization.
    """
    first_name = CharField(required=True)
    last_name = CharField(required=True)
    username = CharField(required=True)
    phone_number = CharField(required=False)


class UpdateNewMemberAtOrgBasicInfoForm(Form):
    """
    A form for updating user information for a new Member at an Organization.

    This form is used in the second step of the process for an Organization user
    to help a person become a Member at that Organization.
    """
    birthdate = DateField(required=True)
    gender = ChoiceField(choices=GENDER_CHOICES, required=False)
    nickname = CharField(required=True)
    email = EmailField(required=True)
