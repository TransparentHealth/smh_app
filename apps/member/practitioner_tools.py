from .fhir_utils import add_key
# from jsonpath_ng import parse


def practitioner_encounter(practitioner, encounter):
    """

    :param practitioner:
    :return: practitioner
    """
    # print("P", len(practitioner))
    # print("E", len(encounter))
    for p in practitioner:
        p = add_key(p, [("earliestDate", str), ("latestDate", str), ("location", list)])

        for e in encounter:
            # run through encounters and find match on practitioner.id or location.id
            participant = get_participant(e)
            location = get_location(e)
            active_date = get_start(e)

            if 'id' in participant:
                if participant['id'] == p['id']:
                   #  print("matched on:", participant, "\nid:", p)
                    if active_date > p['latestDate']:
                        p['latestDate'] = active_date[0:10]
                    if active_date < p['earliestDate']:
                        p['earliestDate'] = active_date[0:10]

                    p['location'].append(location)
    return practitioner


def get_participant(encounter):
    """
    get participant from encounter
    :param practitioner:
    :return:
    """

    if "participant" in encounter:
        id = ""
        if 'individual' in encounter['participant'][0]:
            id_split = encounter['participant'][0]['individual']['reference'].split("/")
            id = id_split[1]

        return {'id': id,
                'reference': encounter['participant'][0]['individual']['reference'],
                'display': encounter['participant'][0]['individual']['display']}
    else:
        # print("encounter:", encounter)
        return {}


def get_location(encounter):
    """
    get location from encounter
    :param encounter:
    :return:
    """
    if "location" in encounter:
        id = ""
        if 'individual' in encounter['location'][0]:
            id_split = encounter['location'][0]['location']['reference'].split("/")
            id = id_split[1]

        return {'id': id,
                'reference': encounter['location'][0]['location']['reference'],
                'display': encounter['location'][0]['location']['display']}
    else:
        return {}


def get_start(encounter):
    """
    get start date from encounter
    :param encounter:
    :return:
    """

    if 'period' in encounter:
        if 'start' in encounter['period']:
            return encounter['period']['start']

    return


def sort_extended_practitioner(practitioner):
    """
    sort on date latestDate
    Then alpha on other practitioners
    :param practitioner:
    :return: practitioner
    """

    uniques = []
    for p in practitioner:
        if find_uniques(p, uniques):
            uniques.append(p)
    return uniques


def find_uniques(p, uniques):
    """

    :param p:
    :param uniques:
    :return:
    """
    unique = True
    for u in uniques:
        if p['id'] == u['id'] and p['latestDate'] == u['latestDate'] and p['location'] == u['location']:
            return False
        elif p['id'] == u['id'] and p['location'] == u['location']:
            return False
        elif p['id'] == u['id']:
            return False

    return unique
