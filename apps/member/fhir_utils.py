# util functions for fhir_requests
# import logging
import json

from datetime import datetime, timezone
from django.conf import settings
from getenv import env
from jsonpath_ng import parse    # , jsonpath
from operator import itemgetter
# from operator import itemgetter as i
# from functools import cmp_to_key
from .constants import VITALSIGNS, TIMELINE
# RECORDS_STU3


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


def path_extract(entry, resource_spec):
    """
    Experiment with jsonpath

    pass in dict from RECORDS_STU3

    field_formats = [{"field": "result", "detail": "$.result[*].display", "format": ""},
                     {"field": "code", "detail": "$.code.coding[*].display", "format": ""},
                     {"field": "effectivePeriod", "detail": "$.effectivePeriod[*]", "format": {"start": 0, "end": 10}}
                    ]
    :param entry:
    :param resource_spec:
    :return:
    """
    # print("\nresource spec:", resource_spec)
    # print('entry:', entry)
    if 'field_formats' in resource_spec:
        field_formats = resource_spec['field_formats']
    else:
        field_formats = []
    if field_formats:
        for e in entry:
            # print("e:", e)
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
    :param columns: list with minus prefix
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
    # for l in listing:
    #     if key in l.keys():
    #         if l[key] == value:
    #             print("l[key = ", value)
    #             return l

    dict_found = next(filter(lambda obj: obj[key] == value, listing), None)
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
    # print("G  Dict:", group_dict)
    entry = []
    # print("isinstance:", type(group_dict))
    for key in group_dict:
        # print("Key:", key, "Value:", group_dict[key])
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
        # print(entry)
        # print("================\n\n")
        return entry
    # We have entries to deal with...
    # {'entry': [{'2020-12-22T09:30:00+00:00': [{'resourceType': 'Encounter', 'id': '672',
    for i in entry['entry']:
        for k in i:
            # print(k, "with value:", i[k])
            big_entry.extend(i[k])
    return {'entry': big_entry}


def concatenate_output(entry):
    """
    Deal with groups of resources in dicts with key of date

    :param entry:
    :return big_entry|
    """
    big_entry = []
#
# entry =
# {'entry': [{'code': {'coding': [{'code': '4050939',
#                                  'display': 'Surgical Pathology',
#                                  'system': 'urn:oid:2.16.840.1.113883.3.4362.1.16'}],
#                      'text': 'Surgical Pathology'},
#             'id': '294',
#             'identifier': [{'assigner': {'display': 'SPHCS-FillerId'},
#                             'system': 'urn:oid:2.16.840.1.113883.3.4362.1.16',
#                             'use': 'official',
#                             'value': '43010234-'},
#                            {'assigner': {'display': 'SPHCS-PlacerId'},
#                             'system': 'urn:oid:2.16.840.1.113883.3.4362.1.16',
#                             'use': 'official',
#                             'value': '43010234-'}],
#             'meta': {'profile': ['http://hl7.org/fhir/StructureDefinition/daf-diagnosticreport']},
#             'resourceType': 'DiagnosticReport',
#
    if isinstance(entry, dict):
        if list(entry.keys())[0] == 'entry':
            sub_entry = entry['entry']

            for e in sub_entry:
                if 'resourceType' in e:
                    # print("adding to big_entry", e['id'])
                    big_entry.append(e)
                else:
                    # print("no resourceType in e")
                    # print(e)
                    # print("-----------")
                    for ek, ev in e.items():
                        for ev_item in ev:
                            if 'resourceType' in ev_item:
                                big_entry.append(ev_item)

            # print("big Entry", len(big_entry))
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
        # print("not a dict so wrap as list in dict with key=entry")
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
        if isinstance(key, str):
            key = [(key, "")]
        for k in key:
            if k[0] in resource:
                pass
            else:
                # print("k[0], k[1]", k[0], ",", k[1])
                if type(k[1]) == str:
                    resource[k[0]] = ""
                elif type(k[1]) == list:
                    resource[k[0]] = []
                elif type(k[1]) == dict:
                    resource[k[0]] = {}
                else:
                    # print('adding ', k[0])
                    resource[k[0]] = ""
        # print("resource keys", resource.keys())
        # print("TYPE:", type(resource))
    return resource


def context_updated_at(context):
    """
    Update Context
    :param context:
    :return context:
    """

    if context['updated_at']:
        context['time_since_update'] = (datetime.now(timezone.utc) - context['updated_at'])
        context['updated_at'] = context['updated_at'].timestamp()

    return context


def timeline_names(timeline):
    """
    Get the names from timeline and return as list
    :param timeline:
    :return: t_names
    """

    t_names = []
    for t in timeline:
        t_names.append(t['name'])

    return t_names


def get_date_from_path(e_item, path_field):
    """
    get the date and return it
    :param e_item:
    :return:
    """

    jp_parsing = parse(path_field)
    result = jp_parsing.find(e_item)
    sort_date = [match.value for match in result]

    if sort_date:
        return sort_date[0:10]
    return "undated"


def date_key(datekey):
    """
    get YYYY-MM-DD from ISO string

    :param datekey:
    :return:
    """
    if isinstance(datekey, list):
        dkey = datekey[0][0:10]
        return dkey
    if isinstance(datekey, str):
        dkey = datekey[0:10]
        return dkey


def dated_bundle(entries):
    """
    get a bundle with 'entry' list
    evaluate using TIMELINE to extract resources with dates
    Create a dict with a key of Date and a value of []
    append record to dict with date key

    sort dict on key with reverse sort by date

    convert dict to list with date as key and list as value

    :param entries:
    :return:
    """
    grouped_entries = {}
    ungrouped = []
    if 'entry' not in entries:
        return entries

    t_names = timeline_names(TIMELINE)

    # We have an entry list to process
    for e in entries['entry']:
        if e['resourceType'] in t_names:

            t = next(filter(lambda obj: obj.get('name') == e['resourceType'], TIMELINE), None)

            if t['datefield']:
                # We have a jsonpath definition to extract a date field from e
                date_k = get_date_from_path(e, t['datefield'])
                # now use the date_key to append e to grouped_entries[date_key]
                if date_k:
                    d_key = date_key(date_k)

                    grouped_entries = add_key(grouped_entries, [(d_key, [])])
                    # print("grouped_entries:", grouped_entries )
                    grouped_entries[d_key].append(e)
                else:
                    ungrouped.append(e)
            else:
                ungrouped.append(e)

    # print("grouped is pre-sort:", type(grouped_entries))
    entries = dict_to_list_on_key(grouped_entries)
    entry = entries['entry']
    # sorted_entry = sorted(entry, key=lambda se: se.keys(), reverse=True)
    sorted_entry = sorted(entry, key=lambda entry: entry.keys(), reverse=True)
    # print('entries-0:', sorted_entry[0])
    # print('entries-1:', sorted_entry[1])
    return {'entry': sorted_entry}


def filter_list(full_list, inc_list=['*'], exc_list=[]):
    """
    Filter the full_list using the exc_list
    then check inc_list for "*" (include everything)
    If no "*" then filter full_list using inc_list

    return the filtered_list

    """

    filtered_list = full_list
    for exc in exc_list:
        if exc in filtered_list:
            filtered_list.remove(exc)

    if "*" in inc_list:
        return filtered_list
    else:
        for inc in inc_list:
            if inc in filtered_list:
                pass
            else:
                filtered_list.remove(inc)
        return filtered_list


def sort_date(entries, resource_spec=None):
    """
    sort the entries by reverse date
    pass in the resource_spec from RECORDS_STU3

    filter out records that don't have the sort field

    :param entries:
    :param resource_spec:
    :return sort_list:
    """
    # print(len(entries))
    # print(entries[0])
    # print("Here is the sequence:\n")

    if resource_spec is None:
        # nothing to do
        return entries

    if 'sort' in resource_spec:
        reverse = reverse_sort(resource_spec['sort'][0])
        date_field_for_sort = strip_sort_indicator(resource_spec['sort'][0])
        sort_date_field = date_field_for_sort.replace("$.", "")
        sort_date_field = sort_date_field.replace(".", "")
        sort_date_field = sort_date_field.replace("[*]", "")
        # print("Sorting on:", sort_date_field)
    else:
        # no sort to do
        return entries

    # filter records that do not have the sort field
    # to avoid an error

    un_sortable = []
    sortable = []

    for e in entries:
        # if 'resourceType' in e:
        #     rt = e['resourceType']
        # else:
        #     rt = "---"
        # if 'id' in e:
        #     id = e['id']
        # else:
        #     id = ".."
        if sort_date_field in e:
            sortable.append(e)
            # pd = e[sort_date_field]
        else:
            un_sortable.append(e)
            # pd = "YYYY-MM-DD"

        # print("{rt}, {id}: {pd}".format(rt=rt, id=id, pd=pd))

#     sort_list = sorted(entries, key=lambda entry: entry[sort_date_field], reverse=True)
    sort_list = sorted(sortable, key=lambda entry: entry[sort_date_field], reverse=reverse)

    if len(un_sortable) > 0:
        sort_list.extend(un_sortable)
    # print("\n\nSorted result:\n")
    # for e in sort_list:
    #     if 'resourceType' in e:
    #         rt = e['resourceType']
    #     else:
    #         rt = "---"
    #     if 'id' in e:
    #         id = e['id']
    #     else:
    #         id = ".."
    #     if sort_date_field in e:
    #         pd = e[sort_date_field]
    #     else:
    #         pd = "YYYY-MM-DD"
    #
    #     print("{rt}, {id}: {pd}".format(rt=rt, id=id, pd=pd))

    return sort_list
