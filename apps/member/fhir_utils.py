# util functions for fhir_requests
import logging
import json

from django.conf import settings
from jsonpath_ng import parse, jsonpath


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


def find_index(dicts, key, value):
    class Null: pass
    for i, d in enumerate(dicts):
        if d.get(key, Null) == value:
            return i
    else:
        raise ValueError('no dict with the key and value combination found')


def find_list_entry(big_list, key, value):
    for l in big_list:
        # print("looking at", l, " with key:", key, " value: ", value)
        if key in l:
            # print("checking", value, "against ", l[key])
            if l[key] == value:
                # print("found value:", value)
                return l
            else:
                # print("no match for ", value)
                pass
    return


def load_test_fhir_data(data):
    """
    load a test fhir structure
    :return: fhir_data
    """
    if settings.VPC_ENV in ['prod', 'staging', 'dev']:
        fhir_data = data.get('fhir_data')
    else:
        # Only run this locally
        f = open("/Volumes/GoogleDrive/My Drive/NewWave/Projects/AFBH-NY/hixny/data_analysis/md_fhir.json", "r")
        fhir_data = json.load(f)
    return fhir_data


def path_extract(entry, resource_spec):
    """
    Experiment with jsonpath

    field_formats = [{"field": "result", "detail": "$.result[*].display", "format": ""},
                     {"field": "code", "detail": "$.code.coding[*].display", "format": ""},
                     {"field": "effectivePeriod", "detail": "$.effectivePeriod[*]", "format": {"start": 0, "end": 10}}
                    ]
    :param entry:
    :param resource_spec:
    :return:
    """


    if 'field_formats' in resource_spec:
        field_formats = resource_spec['field_formats']
    else:
        field_formats = []
    if field_formats:
        for e in entry:
            for ff in field_formats:
                fld = ff['field']
                det = ff['detail']
                fmt = ff['format']
                if fld in e:
                    # print("Field:", e[fld])
                    jp_parsing = parse(det)
                    rslt = jp_parsing.find(e)
                    # print("Result:", det, ">", rslt)
                    results = [match.value for match in rslt]
                    # print(results)
                    result = []
                    for r in results:
                        if isinstance(r, dict):
                            for k, v in r.items():
                                if fmt:
                                    if v[fmt['start']:fmt['end']] not in result:
                                        result.append(v[fmt['start']:fmt['end']])
                                else:
                                    if v not in result:
                                        result.append(v)
                        else:
                            if fmt:
                                if r[fmt['start']:fmt['end']] not in result:
                                    result.append(r[fmt['start']:fmt['end']])
                            else:
                                if r not in result:
                                    result.append(r)
                    if len(result) == 1:
                        result = result[0]
                    # print(result, "<", r)
                    e[fld] = result
    return entry


def sort_json(json_obj, sort_field, sort_value, reverse=True):
    """
    Sort json by a field
    :param json_obj:
    :param sort_field:
    :return: sorted_obj
    """
    sorted_obj = {}
    print("json_obj", len(json_obj))
    print("sort_field:", sort_field)
    print("sort_value:", sort_value)
    print("Reverse:", reverse)
    if json_obj:
        sorted_obj = []
        if sort_field and sort_value:
            sorted_obj = sorted(json_obj, key=lambda x: x[sort_field], reverse=reverse)

    return sorted_obj
