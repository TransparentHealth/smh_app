from django import template
from django.template.defaulttags import register
from ...member.constants import FIELD_TITLES
from ...member.fhir_custom_formats import address

# register = template.Library()

# FIELD_TITLES = [
#     {'profile': 'AllergyIntolerance',
#      'elements': [
#         {'system_name': 'onsetDateTime', "show_name": 'Onset'},
#         {'system_name': 'assertedDate', "show_name": 'Asserted'},
#     ]}
# ]

@register.filter
def friendlyfield(value, resource):
    """
    Value is field_name
    resource is resource_name
    :param value:
    :param resource:
    :return: show_name or value
    """
    if resource:
        for ft in FIELD_TITLES:
            if ft['profile'].lower() == resource.lower():
                for e in ft['elements']:
                    if e['system_name'] == value:
                        return e['show_name']

    return value


@register.filter
def valueformat(value, key):
    """
    Receive value and name of field.
    Check for special formatting for Name, Address or Telecom otherwise return value
    [{'system': 'phone', 'value': '+1-518-438-4483', 'use': 'work'}]
    name: [{'use': 'usual', 'family': 'Randaisi', 'given': ['Deborah', 'L'], 'suffix': ['P.A.C']}]
    :param value:
    :param key:
    :return: value | formatted value based on key
    """

    # print(key, value)
    if key:
        if key.lower() == "address":
            f_value = address(value)
            return f_value

        elif key.lower() == "telecom":
            if isinstance(value, str):
                return value
            f_value = ""

            for t in value:
                use_str = ""
                sys_str = ""
                val_str = ""
                if 'system' in t:
                    sys_str = t['system']
                if 'use' in t:
                    use_str = t['use']
                if 'value' in t:
                    val_str = t['value']
                f_value += "%s - %s: %s. " % (sys_str,
                                              use_str,
                                              val_str)
            return f_value
        elif key.lower() == "name":
            if isinstance(value, str):
                return value
            f_value = ""
            for n in value:
                family_str = ""
                given_str = ""
                suffix_str = ""
                if 'given' in n:
                    given_str = ' '.join([str(x) for x in n['given']])
                if 'suffix' in n:
                    suffix_str = ','.join([str(x) for x in n['suffix']])
                if 'family' in n:
                    family_str = n['family']
                f_value += "%s %s %s" % (given_str,
                                         family_str,
                                         suffix_str)

            return f_value
        else:
            return value