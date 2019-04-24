from django.forms import (
    BooleanField, CharField, ChoiceField, DateField, EmailField, Form, PasswordInput
)


# Choices for a user's gender field in VMI
GENDER_CHOICES = (
    ('', 'Unspecified'),
    ('female', 'Female'),
    ('male', 'Male'),
)
# Choices for when a user verifies the new Member's identity. These also come from VMI.
IDENTITY_VERIFICATION_CLASSIFICATIONS = (
    ('', 'None'),
    ('ONE-SUPERIOR-OR-STRONG+', 'One Superior or Strong+ pieces of identity evidence'),
    ('ONE-STRONG-TWO-FAIR', 'One Strong and Two Fair pieces of identity evidence'),
    ('TWO-STRONG', 'Two Pieces of Strong identity evidence'),
    ('TRUSTED-REFEREE-VOUCH', 'I am a Trusted Referee Vouching for this person'),
    ('KBA', 'Knowledged-Based Identity Verification'),
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


class VerifyMemberIdentityForm(Form):
    """
    A form for verifying a Member's identity.

    This form is used in the third step of the process for an Organization user
    to help a person become a Member at that Organization.
    """
    classification = ChoiceField(choices=IDENTITY_VERIFICATION_CLASSIFICATIONS, required=True)
    description = CharField(required=True)
    expiration_date = DateField(required=True)


class UpdateNewMemberAtOrgAdditionalInfoForm(Form):
    """
    A form for updating user information for a new Member at an Organization.

    This form is used in the fourth step of the process for an Organization user
    to help a person become a Member at that Organization.
    """
    pass


class UpdateNewMemberAtOrgMemberForm(Form):
    """
    A form for a Member to set their password, and accept terms and requests from an Organization.

    This form is used in the last step of the process for an Organization user
    to help a person become a Member at that Organization.
    """
    # Note for BooleanFields: having required=True means the user must check the
    # checkbox in the template.
    accept_terms_and_conditions = BooleanField(required=True)
    give_org_access_to_data = BooleanField(required=True)
    password1 = CharField(widget=PasswordInput, required=True)
    password2 = CharField(widget=PasswordInput, required=True)

    def clean(self):
        """Verify that passwords match each other."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords must match.')
