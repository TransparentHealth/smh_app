from collections import defaultdict
from datetime import datetime
from importlib import import_module
import json

import requests
from django.conf import settings
from django.shortcuts import Http404
from jwkest.jwt import JWT
from apps.org.models import ResourceGrant


def get_prescriptions(data):
    """Returns an id-keyed dict of all prescriptions in the (FHIR) medical data
    * Medication = reference field to join medication resources
        * .id = unique id in this data set
        * .code.text = display name
    * MedicationRequest = records a doctor's request for a medication
        * .medicationReference
            * .reference = "Medication/{id}" that this request is for
            * .display = Medication's display name
        * .requester.agent
            * .reference = "Practioner/{id}" points to a Physician
            * .display = Physician's display name
    * MedicationDispense = records the dispensation of a medication
        * .status = the status of the dispensation ("completed") 
        * .medicationReference{.reference, .display}
    * MedicationStatement = records the prescription itself
        * .status
        * .effectivePeriod{.start, .end}
        * .taken
        * .dosage[0].doseQuantity{.value, .unit}

    Combine records that have the same name, when the date is the same as the previous one or null
    """
    prescriptions = {}
    for entry in data['entry']:
        resource = entry['resource']
        if resource['resourceType'] in [
                'MedicationRequest', 'MedicationStatement', 'MedicationDispense'
        ]:
            id = resource['medicationReference']['reference'].split('/')[-1]
            prescriptions.setdefault(id, {'name': resource['medicationReference']['display']})

            if resource['resourceType'] == "MedicationRequest":
                prescriptions[id]['agent'] = resource.get('requester', {}).get('agent', {})
                prescriptions[id]['request_status'] = resource['status']
            elif resource['resourceType'] == "MedicationDispense":
                prescriptions[id]['dispense_status'] = resource['status']
            elif resource['resourceType'] == "MedicationStatement":
                prescriptions[id]['effectivePeriod'] = {
                    key: datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')  # ISO-formatted
                    for key, value in resource['effectivePeriod'].items()
                }
                prescriptions[id]['dosage'] = {
                    k: v
                    for k, v in resource['dosage'][0]['doseQuantity'].items()
                    if k in ['value', 'unit']
                }
                prescriptions[id]['taken'] = resource['taken']
                prescriptions[id]['statement_status'] = resource['status']
    return prescriptions


def get_member_data(requesting_user, member, resource_name, record_type):
    """Get the data for a member from a resource."""

    # Get the path to the resource class from the settings, based on the
    # resource_name.
    resource_class_path = settings.RESOURCE_NAME_AND_CLASS_MAPPING.get(resource_name, None)
    # If there is not a path for the resource_name, raise an error
    if not resource_class_path:
        raise Http404

    # Is the record_type is not valid, raise an error
    if record_type not in settings.VALID_MEMBER_DATA_RECORD_TYPES:
        raise Http404

    # Users are allowed to request their own data. If the requesting_user is not
    # the member, then check if the requesting_user's Organization has access
    # to this member's resource.
    if requesting_user == member.user:
        resource_module = '.'.join(resource_class_path.split('.')[:-1])
        resource_class_name = resource_class_path.split('.')[-1]
        resource_class = getattr(import_module(resource_module), resource_class_name)

        response = resource_class(member.user).get(record_type)
    else:
        resource_grants = ResourceGrant.objects.filter(
            member=member.user,
            resource_class_path=resource_class_path,
            organization__users=requesting_user)
        if not resource_grants.exists():
            raise Http404
        else:
            resource_grant = resource_grants.first()
        response = resource_grant.resource_class(resource_grant.member).get(record_type)

    # Loop through the content of the response, and put the fields that will
    # need to be shown in the template into a dictionary, where the keys are
    # record types.
    records_dict = defaultdict(list)
    for record in json.loads(response.content)['entry']:
        # These are the data that will be needed for the template
        record_data = {
            'date': record['resource']['assertedDate'],
            'code': record['resource']['code']['coding'][0]['code'],
            'diagnosis': record['resource']['code']['text'],
            'provider': '',
        }
        # Add the data into the records_dict
        records_dict[record['resource']['resourceType']].append(record_data)

    # Loop through the valid record types, and create a list of dictionaries,
    # where the keys are the record types, and the values are the data that will
    # be shown in the template for that record type. Note: the results list can
    # include record types that have no data, in which case just their 'name'
    # and 'icon_src' are returned, so those can still be rendered in the
    # template.
    results = []
    for valid_record_type in settings.VALID_MEMBER_DATA_RECORD_TYPES:
        # Find the record type name that will be used in the template
        if valid_record_type in settings.MEMBER_DATA_RECORD_TYPE_MAPPING.keys():
            record_type_name = settings.MEMBER_DATA_RECORD_TYPE_MAPPING[valid_record_type]
        else:
            record_type_name = valid_record_type

        # Create a dictionary of data for this record type
        record_type_data = {
            'name': record_type_name.replace('_', ' ').title(),
            'icon_src': '/images/icons/{}.png'.format(record_type_name.replace('_', '-')),
        }
        if valid_record_type in records_dict:
            record_type_data['records'] = records_dict[valid_record_type]
        else:
            record_type_data['records'] = []
        record_type_data['total'] = len(record_type_data['records'])

        # Add the dictionary of data for this record type to the results
        results.append(record_type_data)

    return results


def fetch_member_data(member, provider):
    '''Fetch FHIR data from HIXNY data provider (sharemyhealth)'''
    url = f"{settings.SOCIAL_AUTH_SHAREMYHEALTH_HOST}/hixny/api/fhir/stu3/Patient/$everything?refresh=true"
    sa = member.user.social_auth.filter(provider=provider).first()
    if sa is not None:
        access_token = sa.extra_data.get('access_token')
        if access_token is not None:
            r = requests.get(url, headers={'Authorization': 'Bearer %s' % access_token})
            if r.status_code == 200:
                return r.json()
    # fallback: empty member data
    return {'entry': []}


def get_resource_data(data, resource_type):
    return [
        item['resource']
        for item in data.get('entry', [])
        if item['resource']['resourceType'] == resource_type
    ]


def get_id_token_payload(user):
    # Get the ID Token and parse it.
    try:
        vmi = user.social_auth.filter(provider='vmi')[0]
        extra_data = vmi.extra_data
        if 'id_token' in vmi.extra_data.keys():
            id_token = extra_data.get('id_token')
            parsed_id_token = JWT().unpack(id_token)
            parsed_id_token = parsed_id_token.payload()
        else:
            parsed_id_token = {'sub': '', 'ial': '1'}

    except Exception:
        parsed_id_token = {'sub': '', 'ial': '1'}

    return parsed_id_token
