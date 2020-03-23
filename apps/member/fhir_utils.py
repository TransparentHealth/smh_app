# util functions for fhir_requests
import logging
import json

from django.conf import settings
from jsonpath_ng import parse, jsonpath
from operator import itemgetter
from operator import itemgetter as i
from functools import cmp_to_key
from .constants import VITALSIGNS


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
        pass
        # Only run this locally
        # f = open("/Volumes/GoogleDrive/My Drive/NewWave/Projects/AFBH-NY/hixny/data_analysis/md_fhir.json", "r")
        # fhir_data = json.load(f)
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


def sort_json(json_obj, columns):
    """
    Sort json by fields
    https://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys

    Supports a single sort_field passed as a list
    Removes any dicts that don't have the sort_field and appends them to the end after sorting
    :param json_obj: List
    :param sort_fields: list with minus prefix
    :return: result | json_obj
    """

    if columns:
        sortable_obj = []
        unsortable_obj = []
        for j in json_obj:
            if strip_sort_indicator(columns[0]) in j:
                # print(columns[0], "may be sortable:", type(j[columns[0]]))
                if type(j[strip_sort_indicator(columns[0])]) in [list, dict]:
                    # print("Excluding a ", type(j[columns[0]]))
                    unsortable_obj.append(j)
                else:
                    # print('sorting:', j[columns[0]])
                    sortable_obj.append(j)
            else:
                unsortable_obj.append(j)

        if len(columns) == 1:
            result = []
            if reverse_sort(columns[0]):
                result = sorted(sortable_obj, key=itemgetter(strip_sort_indicator(columns[0])), reverse=True)
            else:
                # print("standard sort:", columns[0], '/', sortable_obj)
                result = sorted(sortable_obj, key=itemgetter(strip_sort_indicator(columns[0])), reverse=False)
                # print(len(result))
            for u in unsortable_obj:
                result.append(u)
            # print(len(result))
            return result

        else:
            result = []
            # Need to add second column sort capability
            if reverse_sort(columns[0]):
                # print("reverse sort:", strip_sort_indicator(columns[0]))
                # print(json_obj[0])
                result = sorted(sortable_obj, key=itemgetter(strip_sort_indicator(columns[0])), reverse=True)
            else:
                # print("sort:", columns[0])
                result = sorted(sortable_obj, key=itemgetter(strip_sort_indicator(columns[0])), reverse=False)

            for u in unsortable_obj:
                result.append(u)
            return result
    else:
        # print('No sort')
        return json_obj


def strip_sort_indicator(sort_field):
    """
    Remove the leading '-'
    :param sort_field:
    :return: result
    """

    if sort_field:
        if sort_field[:1] == '-':
            return sort_field[1:]
        else:
            return sort_field

    else:
        return


def reverse_sort(sort_field):
    """
    Check for leading - to indicate reverse sort
    :param sort_field:
    :return: True | False
    """

    if sort_field:
        if sort_field[:1] == '-':
            return True

    return False


def rebuild_field_path(sort_field, resource):
    """
    convert dot connected fields into a valid field reference
    :param sort_field:
    :return: path_to_field
    """

    sorted = strip_sort_indicator(sort_field)

    split_sorted = sorted.split()

    sort_with_this = ""
    for s in split_sorted:
        if s in resource:
            sort_with_this = sort_with_this + s

    return sort_with_this


def create_vital_sign_view_by_date(fhir_entries):
    """
    use the grouped vitalsigns

    create a single record based on the vital signs from
    """

    vs_view = []
    vs_item = {}
    vs_deduplicate = []
    vitalsigns = group_vitalsigns_by_date(fhir_entries)
    for k, v in vitalsigns:
        # For each start date we must build a view
        for f in v:
            # Get each vitalsign fhir entry dict
            pass
            if 'code' in f:
                if 'coding' in f['code']:
                    for coding in f['code']['coding'] and 'valueQuantity' in f:
                        if coding['code'] in VITALSIGNS:

                            vs_item['code'] = coding['code']
                            vs_item['display'] = coding['display']
                            vs_item['value'] = f['valueQuantity']['value']
                            vs_item['unit'] = f['valueQuantity']['unit']



    return vs_view


def group_vitalsigns_by_date(fhir_entries):
    """
    Build a Vital Signs Dict by date
    Consolidate entries for a date into a single record
    :param fhir_entries:
    :return: fhir_bundle
    """

    vitalsigns = {}

    # Loop through vital signs and group records by effectivePeriod
    # vitalsigns = {
    #    "{YYYY-MM-DD}"

    #     "entries": [
    #       {fhir_entries for effectivePeriod.start},
    #       ]
    # }

    for f in fhir_entries:
        vs = {}
        if 'effectivePeriod' in f:
            if 'start' in f['effectivePeriod']:
                # we can work with the record
                startd = f['effectivePeriod']['start'][0:10]
                if startd in vitalsigns:
                    vitalsigns[startd] = f

    #             vs = find_key_value_in_list(vitalsigns, 'effectivePeriod', f['effectivePeriod'['start']])
    #             vs['date'] = f['effectivePeriod']['start']
    #             if 'code' in f:
    #                 if 'coding' in f['code']:
    #                     for c in f['code']['coding']:
    #                         vs[]

    return vitalsigns


def find_key_value_in_list(listing, key, value):
    """
    look for key with value in list and return dict
    :param listing:
    :param key:
    :param value:
    :return: dict_found
    """
    dict_found = next(filter(lambda obj: obj.get(key) == value, listing), None)
    if dict_found:
        return dict_found
    else:
        return {}