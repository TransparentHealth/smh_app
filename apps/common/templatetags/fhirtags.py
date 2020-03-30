# from django import template
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
        elif key.lower() == 'dosage':
            #  "doseQuantity": {
            #                 "value": 200,
            #                 "unit": "MG",
            #                 "system": "http://unitsofmeasure.org/ucum.html"
            #             }
            f_value = ""
            for i in value:
                if isinstance(i, int) or isinstance(i, float):
                    if i == 0:
                        pass
                    else:
                        f_value += str(i) + " "
                else:
                    if 'http' in i.lower():
                        pass
                    else:
                        f_value += str(i) + " "

            return f_value
        elif key.lower() == 'dataabsentreason':
            if isinstance(value, dict):
                return value['coding'][0]['display']
            else:
                return value
        elif key.lower() == 'valuequantity':
            return str(value['value']) + " " + value['unit']
        elif key.lower() == 'valuestring':
            return value
        elif key.lower() == 'interpretation':
            return value['coding'][0]['display']
        elif key.lower() == 'referencerange':
            f_value = ""
            for i in value:
                if isinstance(i, dict):
                    for k in i.items():
                        if k[0].lower() == 'text':
                            f_value += str(k[1])
                        else:
                            f_value += str(k[0])
                            f_value += ": " + str(k[1]['value'])
                            f_value += " " + str(k[1]['unit']) + " "
                elif isinstance(i, list):
                    for ll in i:
                        for d in ll:
                            f_value += str(d.key())
                            f_value += str(d['value'])
                            f_value += " "
                            f_value += d['unit'] + ", "

            return f_value
        else:
            return value
