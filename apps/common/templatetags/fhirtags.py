# from django import template
from django.template.defaulttags import register
from ...member.constants import FIELD_TITLES, RECORDS_STU3
from ...member.fhir_custom_formats import address
from ...member.fhir_utils import find_key_value_in_list

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
    concat_key = key.split('.')
    if len(concat_key) > 1:
        # Pass in either the key of the field
        # or pass in resource.key to enable a resource lookup.
        key = concat_key[1]
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
            for v in value:
                if isinstance(v, int) or isinstance(v, float):
                    if v == 0:
                        pass
                    else:
                        f_value += str(v) + " "
                elif isinstance(v, str):
                    if 'http' in v.lower():
                        pass
                    else:
                        f_value += str(v) + " "
                elif isinstance(v, list):
                    for d, vv in v.items():
                        if isinstance(vv, int) or isinstance(vv, float):
                            if vv == 0:
                                pass
                            else:
                                f_value += str(vv) + " "
                        elif isinstance(vv, str):
                            if 'http' in vv.lower():
                                pass
                            else:
                                f_value += str(vv) + " "
            return f_value
        elif key.lower() == 'medicationreference':
            f_value = value
            # lookup field_formats
            # concat_key should have a resource name
            if len(concat_key) > 1:
                resource = concat_key[0]
            else:
                resource = None
            if resource:
                # look up field_format in RECORDS_STU3

                f_value = "Medication: " + value['display']
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


@register.filter
def resourceview(resource, member_id, viewer="default"):
    """
    Take a resource and display it
    use RECORDS_STU3 to control display

    {'name': 'MedicationStatement', 'slug': 'medicationstatement', 'call_type': 'fhir', 'resources': ['MedicationStatement'], 'display': 'Medication Statement',
     'headers': ['id', 'medicationReference', 'dosage', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'status', 'effectivePeriod', 'subject', 'taken'],
     'field_formats': [
         {'field': 'medicationReference', 'detail': '$.medicationReference.display', 'format': ''},
         {'field': 'effectivePeriod', 'detail': '$.effectivePeriod[*]', 'format': {'start': 0, 'end': 10}},
         {'field': 'informationSource', 'detail': '$.informationSource.display', 'format': ''},
         {'field': 'dosage', 'detail': '$.dosage[*].doseQuantity', 'format': ''},
     ],
     'sort': ['$.medicationReference.display'],
     'group': ['$.medicationReference.display'],
     'views': ['record', 'records']
     },

    :param resource:
    :param viewer:
    :return: None or html_output string
    """

    resourceType = resource['resourceType']

    view_format = find_key_value_in_list(RECORDS_STU3, 'name', resourceType)
    # print("viewport:", view_format)

    if not view_format:
        return
    # We can format output
    html_output = ""

    html_output += "<td><img src='/static/images/icons/{}.png' alt='{}' height='14' width='14'>" \
                   "&nbsp&nbsp{}".format(view_format['name'],
                                         view_format['display'],
                                         view_format['display'])

    html_output += "</td><tr><td>"
    for key, value in resource.items():
        show = False
        if key in view_format['headers']:
            show = True
        elif key in view_format['exclude']:
            show = False
        elif "*" in view_format['headers']:
            show = True
        else:
            show = False
        if show:
            if value == resourceType:
                pass
            if key == "id":
                html_output += "<a href='' class='modal-link' data-toggle='modal' data-target='#record-detail--modal' " \
                               "data-url='/member/{}/data/{}/{}'>" \
                               "{}</a> ".format('1', resourceType, value, value)
            else:
                if key == 'dosage':
                    if isinstance(value, list):
                        html_output += key + ": "
                        for ii in value:
                            for kk, vv in ii.items():
                                if kk.lower() == 'dosequantity':
                                    html_output += str(vv['value']) + " " + vv['unit'] + " "
                                elif kk.lower() == 'timing':
                                    html_output += str(vv) + " "
                else:
                    html_output += "{}".format(valueformat(value, "medicationReference." + key))

            # html_output += "{}:{} ".format(key, value)

    html_output += "</td></tr>"

    return html_output
