# Parse different FHIR Profiles
# FHIR Version 3.0.2


OBSERVATiON_PROFILE = {"resourceType": "Observation",
                       "displayFields": ["text",
                                         "subject.display",
                                         "valueQuantity.value",
                                         "valueQuantity.unit",
                                         "status"]
 }

# {'code': {'coding': [{'code': '9279-1',
#                       'display': 'Respiratory Rate',
#                       'system': 'http://loinc.org'}],
#  'text': 'Respiratory Rate'},
#  'effectivePeriod': {'start': '2014-12-17T08:03:00+00:00'},
#  'id': '335',
#  'resourceType': 'Observation',
#  'status': 'final',
#  'valueQuantity': {'unit': '/min', 'value': 16}
# }


def get_display_fields(resourceType):
    """
    process resource for display
    """

    return resourceType
