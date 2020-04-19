# from django import template
from django.template.defaulttags import register
from ...member.constants import FIELD_TITLES, RECORDS_STU3
from ...member.fhir_custom_formats import (dt_address,
                                           dt_telecom,
                                           dt_name,
                                           dt_dosage,
                                           dt_medicationreference,
                                           dt_referencerange,
                                           dt_reference)
from ...member.fhir_utils import (find_key_value_in_list,
                                  filter_list,
                                  path_extract
                                  )

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
def valueformat(value, format_list):
    """
    Receive value and name of field.
    Check for special formatting for Name, Address or Telecom otherwise return value

    format_list = "member." + member_id + "." + resourceType + "." + key
    key is a field name or is a resourceType.key structure.
    If resourceType.key then lookup resourceType in RECORDS_STU3
    [{'system': 'phone', 'value': '+1-518-438-4483', 'use': 'work'}]
    name: [{'use': 'usual', 'family': 'Randaisi', 'given': ['Deborah', 'L'], 'suffix': ['P.A.C']}]
    :param value:
    :param format_list:
    :return: value | formatted value based on key
    """

    # print("\n", format_list, value)
    concat_key = format_list.split('.')
    # Pass in either the key of the field
    # or pass in resource.key to enable a resource lookup.
    key = ""
    resource = ""
    member_id = ""
    key_sequence = [key, resource, member_id]
    count = 0
    for r in reversed(concat_key):
        key_sequence[count] = r
        count += 1

    # print("Concat_key:", concat_key)
    key = key_sequence[0]
    resource = key_sequence[1]
    member_id = key_sequence[2]

    # print("Key:", key)

    if key:
        if key.lower() == "address":
            return dt_address(value)

        elif key.lower() == "telecom":
            return dt_telecom(value)

        elif key.lower() == "name":
            return dt_name(value)
        elif key.lower() == 'dosage':
            return dt_dosage(value)
        elif key.lower() == 'medicationreference':
            # print("Working on", key, ": ", value)
            # f_value = value
            # lookup field_formats
            # concat_key should have a resource name
            # print("\n\nRESOURCE:", resource)
            # print("calling dt_medicationreference with Resource:", resource, ", value:", value)
            return dt_medicationreference(value, member_id, resource)

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
            return dt_referencerange(value)
        elif key.lower() == 'requester':
            if 'display' in value['agent']:
                return dt_reference(value['agent'], member_id)
        # elif key.lower() == "result":
        #     return dt_reference(value[0], member_id)
        elif key.lower() == 'participant':
            if 'display' in value[0]['individual']:
                return dt_reference(value[0]['individual'], member_id)
        elif key.lower() == 'location':
            if 'display' in value[0]['location']:
                return dt_reference(value[0]['location'], member_id)
        else:
            # print("value:", value, " type:", type(value), " for: ", key)
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

    resource is a complete FHIR resource

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
    res = path_extract([resource, ], view_format)[0]
    # and insert the resulting content into html output

    # and return to the view

    html_output = ""

    html_output += "<td><a href='' class='modal-link' data-toggle='modal' data-target='#record-detail--modal'"
    html_output += "       data-url='/member/{member_id}/data/{resource_type}/{resource_id}'>" \
                   "       <img src='/static/images/icons/{resource_type}.png' " \
                   "            alt='{resource_type}' height='20' width='20'> " \
                   "       <img src='/static/images/icons/popup.png' " \
                   "            alt='More info' height='20' width='20'> " \
                   "</a> </td>".format(member_id=member_id,
                                       resource_type=resourceType,
                                       resource_id=res['id'],)

#     print("Titles=", title_fields, "\n", "Fields:", fields)
    for key, value in res.items():
        if key in fields:
            if key != 'id':
                # We want to process the field
                # print("KEY:", key, ":", value)
                html_output += "<td>{result}</td>".format(result=valueformat(value, str(member_id) + '.' + resourceType + '.' + key))
                # print("Here is html_output:", html_output)
                # if "{member_id}" in html_output:
                #     print("got to replace {member_id} with ", member_id)
                #     html_output.replace("_-_member_id_-_", str(member_id))
        else:
            pass
            # print("no match for key in fields:", key, "/", fields)

    template_html = """
    <tr>{t}
    </tr>
    <tr>
    {h}
    </tr>
    """.format(t=titles_line, h=html_output)

    # template_html.replace("_-_member_id_-_", str(member_id))
    # print("\nTEMPLATE HTML:\n", template_html)

    return template_html
