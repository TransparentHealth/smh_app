from django.forms import CharField, ChoiceField, DateField, EmailField, Form


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
