# custom data type handler
# from math import remainder
from django.utils.safestring import mark_safe
from django.utils.html import escape
from .constants import PREFERRED_LANGUAGE, PRECISION, DISPLAY_US, METRIC_CONVERSION


def dt_address(address, member_id=None):
    """
    Address as List convert to strings
         "address": [
        {
            "use": "work",
            "line": [
                "80 Wolf Road"
            ],
            "city": "Albany",
            "state": "NY",
            "postalCode": "12205",
            "country": "US"
        }
    ]
    :param address:
    :return:
    """
    address_str = ""
    if isinstance(address, list):
        # print("list:", address)
        for a in address:
            address_str = address_str + address_dict(a)
            if a in ['home', 'work', 'temp', 'old']:
                address_str = address_str + ":"
            else:
                address_str = address_str + " "
    elif isinstance(address, dict):
        # print("dict:", address)
        address_str = address_str + address_dict(address) + " "
    else:
        # print('string:', address)
        address_str = str(address)
    return address_str


def dt_communication(value):
    """
    translate communication language to readable description

    :param value:
    :return f_value:
    """
    # print("Value:", value)
    for i in PREFERRED_LANGUAGE:
        if value.lower() in i:
            return i[value.lower()]
    return value


def dt_telecom(value, member_id=None):
    """
    Format Telecom type field
    :param value:
    :return: string
    """

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


def dt_name(value, member_id=None):
    """
    Format name complex data type

    :param value:
    :param f_value
    """
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


def dt_dosage(value, member_id=None):
    """
    Format Dosage Complex data type
    :param value:
    :return: f_value
    """
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
        elif isinstance(v, dict):
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


def dt_medicationreference(value, member_id=None, resource=None):
    """
    Format MedicationReference Complex Data Type
    :param value:
    :return f_value:
    """
    # print("\nResource:", resource, ", Value:", value)
    f_value = value
    if resource:
        # print("Value:", value)
        # look up field_format in RECORDS_STU3
        if type(value) == list:
            f_value = ""
            # f_value = "Medication: "
            for v_l in value:
                if 'display' in v_l:
                    # f_value += v_l['display'] + " "
                    f_value += dt_reference(v_l, member_id) + " "
        elif type(value) == dict:
            if 'display' in value:
                # f_value = value['display']
                f_value = dt_reference(value, member_id)
                # f_value = "Medication: " + value['display']
    else:
        # print("ELSE Value:", value)
        # look up field_format in RECORDS_STU3
        f_value = value
        if type(value) == list:
            f_value = ""
            # f_value = "Medication: "
            for v_l in value:
                if 'display' in v_l:
                    # f_value += v_l['display'] + " "
                    f_value += dt_reference(v_l, member_id) + " "
        elif type(value) == dict:
            # print("Dealing with DICT")
            if 'display' in value:
                # print("we have a display")
                # f_value = value['display']
                f_value = dt_reference(value, member_id)
                # f_value = "Medication: " + value['display']
    return f_value


def dt_referencerange(value, member_id=None):
    """
    format referenceRange complex data type
    :param value:
    :return f_value:
    """
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


def dt_reference(display_dict, member_id=None):
    """
    Format a Reference
    :return:
    """
    if 'reference' in display_dict:
        if ('text' in display_dict):
            disp = display_dict['text']
        elif ('display' in display_dict):
            disp = display_dict['display']
        else:
            disp = display_dict['reference']

        f_value = "<a href='' class='modal-link' data-toggle='modal' data-target='#record-detail--modal' "
        f_value += "data-url='/member/{member_id}/data/{reference}"\
                   "?pretty=True' ".format(member_id=member_id,
                                           reference=display_dict['reference'])

        f_value += "alt='{disp}' >{disp}</a>".format(disp=escape(disp))
        # print(f_value)
    return mark_safe(f_value)


def dt_valuequantity(value):
    """
    Convert valueQuantity to US from metric

    :return f_value:
    """
    f_value = ''
    default_value = str(value['value']) + " " + value['unit']
    if 'unit' in value:
        # check for conversion
        if DISPLAY_US:
            # print("convert to us format")
            mc = check_conversion(value['unit'])
            # print("mc:", mc)
            if mc:
                # print("we found ", value['unit'], " in ", METRIC_CONVERSION)
                if mc[0].lower() == "ft.in":
                    feet = int((value['value'] * mc[1]) / 12)
                    inches = int((((value['value'] * mc[1]) / 12) % feet) * 12)
                    num_str = str(feet) + "ft " + str(inches) + "in"
                    f_value = num_str
                else:
                    num_str = "{:.{precision}f}".format(value['value'] * mc[1], precision=PRECISION)
                    f_value = str(num_str) + " " + mc[0]
                return f_value
            else:
                return default_value
        else:
            # print("Not converting - DISPLAY_US:", DISPLAY_US)
            return default_value
    else:
        # print("no unit in ", value)
        return value

    return f_value


def address_dict(address, show_country=False):
    """
    Address as dict
    :param address:
    :return:
    """
    address_str = ""
    if isinstance(address, dict):
        # print("we have a dict", address)
        for k, v in address.items():
            if k == "use":
                address_str = address_str + v + ": "
            elif k == "line":
                address_str = address_str + list_to_str(v) + " "
            elif k in ['city', 'state', 'postalCode']:
                address_str = address_str + v + " "
            elif k == "country" and show_country:
                address_str = address_str + v
    elif isinstance(address, list):
        # print("we have a list: ", address)
        address_str = address_str + list_to_str(address) + ", "
    else:
        address_str = str(address)
    return address_str


def list_to_str(block, delim=", "):
    """
    Convert list to string with delimiter
    :param block:
    :param delim:
    :return: list_str
    """

    list_str = ""
    for b in block:
        # print("processing:", block)
        if len(list_str) > 0:
            list_str = list_str + delim
        list_str = list_str + str(b)

    return list_str


def check_conversion(unit_value):
    """
    look up a conversion value

    :param unit_value:
    :return conversion:
    """
    for mc in METRIC_CONVERSION:
        if unit_value in mc:
            for k, v in mc.items():
                # print("MC", mc, "values:", v)
                return v
