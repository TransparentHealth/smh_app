# from django import template
from django.template.defaulttags import register
from ...member.constants import FIELD_TITLES, RECORDS_STU3
from ...member.fhir_custom_formats import address
from ...member.fhir_utils import (find_key_value_in_list,
                                  filter_list,
                                  path_extract)

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
                f_value += "{first} {surname} {suffix}".format(first=given_str,
                                                               surname=family_str,
                                                               suffix=suffix_str)
            return f_value
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
        elif key == 'medicationReference':
            print("Working on", key)
            f_value = value
            # lookup field_formats
            # concat_key should have a resource name
            if len(concat_key) > 1:
                resource = concat_key[0]
            else:
                resource = None
            print("\n\nRESOURCE:", resource)
            if resource:
                print("Value:", value)
                # look up field_format in RECORDS_STU3
                if type(value) == list:
                    f_value = "Medication: "
                    for v_l in value:
                        if 'display' in v_l:
                            f_value += v_l['display'] + " "
                elif type(value) == dict:
                    if 'display' in value:
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
            print("some other key:", key, " and value:", value)
            return value


@register.filter
def repeat_resourceview(resource, member_id):
    """
    Call resourceview with changed=False
    :param resource:
    :param member_id:
    """
    return resourceview(resource, member_id, changed=False)


@register.filter
def resourceview(resource, member_id, changed=True):
    """
    Take a resource and display it
    use RECORDS_STU3 to control display
    If changed = True we can repeat

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
    :param member_id:
    :param changed: 0 | 1
    :param viewer:
    :return: None or html_output string
    """

    # get the FHIR resourceType from the record
    resourceType = resource['resourceType']

    # Use the resourceType to lookup the view controller for the resource
    view_format = find_key_value_in_list(RECORDS_STU3, 'name', resourceType)
    # print("viewport:", view_format)

    if not view_format:
        return
    # We can format output

    titles_line = ""
    # Use the view_format to tailor the resource display
    # get the fields to display
    fields = filter_list(list(resource.keys()),
                         view_format['headers'],
                         view_format['exclude'])

    # print("display fields:", fields)
    # Get the friendly names for fields
    if changed:
        # this is a new resource
        friendly_field_def = find_key_value_in_list(FIELD_TITLES, 'profile', resourceType)
        ffd = not friendly_field_def
        # ffd is True if friendly_field_def is empty
        title_fields = []
        title_fields.extend(fields)
        if ffd:
            pass
        else:
            for e in friendly_field_def['elements']:
                if e['system_name'] in title_fields:
                    ix = title_fields.index(e['system_name'])
                    title_fields[ix] = e['show_name']

        # create the titles_line
        for t in title_fields:
            if t == title_fields[0]:
                titles_line += "<td><b>{r_type}<br/>{title}</b></td>".format(r_type=resource['resourceType'],
                                                                         title=t)
            else:
                titles_line += "<td><b>{title}</b></td>".format(title=t)
    # convert the fields from the resource based on format rules
    res = path_extract([resource, ], view_format)
    # and insert the resulting content into html output

    # and return to the view

    html_output = ""

    html_output += "<td><a href='' class='modal-link' data-toggle='modal' data-target='#record-detail--modal'"
    html_output += "       data-url='/member/{member_id}/data/{resource_type}/{resource_id}'>" \
                   "       <img src='/static/images/icons/{resource_type}.png' " \
                   "            alt='{resource_type}' height='14' width='14'> " \
                   "{resource_id}</a> </td>".format(member_id=member_id,
                                                    resource_type=resourceType,
                                                    resource_id=resource['id'],)

#     print("Titles=", title_fields, "\n", "Fields:", fields)
    for key, value in resource.items():
        if resourceType == "MedicationStatement":
            print("resource:", resource, "\n", "key:", key, "value:", value)
        if key in fields:
            if key != 'id':
                # We want to process the field
                print("KEY:", key)
                html_output += "<td>{result}</td>".format(result=valueformat(value, "medicationStatement." + key))
        else:
            print("no match for key in fields:", key, "/", fields)


    template_html = """
    <tr>{}
    </tr>
    <tr>
    {}
    </tr>
    """.format(titles_line, html_output)

    return template_html
