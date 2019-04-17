from django.forms import CharField, Form


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
