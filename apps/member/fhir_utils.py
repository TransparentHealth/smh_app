# util functions for fhir_requests
import logging
import json


def resource_count(entries=[]):
    """
    Count for each type of resource
    count = [{resourceType: instances}, ...]

    :param entries:
    :return: counts:  dictionary of counts
    """
    count = {}

    for e in entries:
        if "resourceType" in e:
            if e['resourceType'] in count:
                val = count[e['resourceType']]
                count.update([(e['resourceType'], val + 1)])
            else:
                count.update([(e['resourceType'], 1)])
    return count
