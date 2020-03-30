# util functions for fhir_requests
# import logging
import json

from django.conf import settings
from getenv import env
from jsonpath_ng import parse    # , jsonpath
from operator import itemgetter
# from operator import itemgetter as i
# from functools import cmp_to_key
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
    class Null:
        pass
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
        if settings.VPC_ENV.lower() == 'local':
            patch_file = env('FHIR_PATCH_FILE', None)
            if patch_file:
                # Only run this locally
                f = open(patch_file, 'r')
                fhir_data = json.load(f)
            else:
                fhir_data = data.get('fhir_data')
        else:
            fhir_data = data.get('fhir_data')
    return fhir_data


# def load_test_fhir_data(data):
#     """
#     load a test fhir structure
#     :return: fhir_data
#     """
#     if settings.VPC_ENV in ['prod', 'staging', 'dev']:
#         fhir_data = data.get('fhir_data')
#     else:
#         pass
#         # Only run this locally
#         # f = open("/Volumes/GoogleDrive/My Drive/NewWave/Projects/AFBH-NY/hixny/data_analysis/md_fhir.json", "r")
#         # fhir_data = json.load(f)
#         fhir_data = data.get('fhir_data')
#     return fhir_data


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
    vs_deduplicate.append('')
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
        vs = vs
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


def view_filter(all_records, view=None):
    """
    Filter RECORDS_STU3 on key = view
    :param all_records:
    :param view:
    :return: view_records
    """
    if view is None:
        # nothing to filter
        return all_records
    else:
        # filter on view
        records = []
        for a in all_records:
            # print('filtering ', a)
            if 'views' in a:
                if view in a['views']:
                    # print('found', view)
                    records.append(a)
        return records


def value_in(resource, value):
    """
    check for field in resource
    :param resource:
    :param value:
    :return: True | False
    """
    if value in resource:
        if isinstance(resource[value], dict):
            if resource[value] == {}:
                return False
            else:
                return True
        elif isinstance(resource[value], list) or isinstance(resource[value], str):
            if len(resource[value]) == 0:
                return False
            else:
                return True
    else:
        return False


def dict_to_list_on_key(group_dict, ungrouped=[]):
    """
    split a dict with a format of {'key0': [list of value 0 items], 'key1': [list of value1 items]}
    to entry = [{'key0': ['list', ' of', 'value0', ' items']},{'key1': ['list', ' of', 'value1', ' items']}]
    """
    entry = []
    for key in group_dict:
        entry.append({key: group_dict[key]})
    if ungrouped:
        # Add on anything that wasn't grouped.
        entry.extend(ungrouped)
    return {'entry': entry}


def groupsort(entry, resource):
    """

    :param entry:
    :param resource:
    :return:
    """

    if not resource:
        return entry

    # We have a resource definition
    if not value_in(resource, 'group'):
        return entry
    # We have a group definition
    grouped = {}
    # print('group', resource['group'][0])
    # print(entry[0])
    ct = 0
    ungrouped = []
    for e in entry:
        ct += 1
        jp_parsing = parse(resource['group'][0])
        result = jp_parsing.find(e)
        # print("count:", ct, "Result:", resource['group'][0], ">", result)
        group_key = [match.value for match in result]
        # print("group_key:", group_key)
        if len(group_key) > 0:
            # we have group_key = ['key']
            if grouped == {}:
                grouped[group_key[0]] = [e, ]
            elif group_key[0] not in grouped.keys():
                grouped[group_key[0]] = [e, ]
            else:
                grouped[group_key[0]].append(e)
        else:
            # No match on group_key
            ungrouped.append(e)

    # print(type(grouped))
    group_entry = dict_to_list_on_key(grouped, ungrouped)
    if not value_in(resource, 'sort'):
        # nothing to sort
        return group_entry

    reverse = reverse_sort(resource['sort'][0])
    # sort_field = strip_sort_indicator(resource['sort'][0])

    group_entry['entry'].sort(key=lambda d: list(d.keys()), reverse=reverse)
    # print('group_entry[entry][0]:', group_entry['entry'][0])
    return group_entry


def concatenate_lists(entry):
    """
    take a list with a key (e.g. date) that has a list of resourceTypes entries
    Copy all lists to a single list

    entry should be:
    {'entry': [{'2020-12-22T09:30:00+00:00': [{'resourceType': 'Encounter', 'id': ...
    :param entry:
    :return: big_entry
    """

    big_entry = []
    if 'entry' not in entry:
        return entry
    # check if we have a key of resourceType in entry. If we do then we don't a grouped key
    # so we return entry
    if len(entry['entry']) > 0 and 'resourceType' in entry['entry'][0].keys():
        # print('not a grouped dict')
        return entry
    # We have entries to deal with...
    # {'entry': [{'2020-12-22T09:30:00+00:00': [{'resourceType': 'Encounter', 'id': '672',
    for i in entry['entry']:
        for k in i:
            # print(k, "with value:", i[k])
            big_entry.extend(i[k])
    return {'entry': big_entry}


def entry_check(entry):
    """
    check if entry is a dict and has a key entry.
    If list return dict {'entry': entry}
    :param entry
    :return: entry_dict
    """
    # print("entry type:", type(entry))
    if isinstance(entry, dict):
        # print("keys:", entry.keys())
        if 'entry' in entry:
            # print("returning entry")
            # print(entry)
            return entry
        # print('not an entry list')
        # print("entry:", entry)
    else:
        return {'entry': entry}


def add_key(resource, key=[]):
    """
    Add a key to a resource if it does not exist
    key contains tuples (fieldname, instancetype)
    :param resource:
    :param key: list
    :return: resource
    """

    if isinstance(resource, dict):
        for k in key:
            if k[0] in resource:
                pass
            else:
                if k[1] == str:
                    resource[k[0]] = ""
                elif k[1] == list:
                    resource[k[0]] = []
                elif k[1] == dict:
                    resource[k[0]] = {}
    return resource


