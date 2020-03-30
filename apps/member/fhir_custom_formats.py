# custom data type handler


def address(address):
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