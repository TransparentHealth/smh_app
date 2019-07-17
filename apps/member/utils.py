import hashlib
import base64
from datetime import datetime
import dateparser

from memoize import memoize
import requests
from django.conf import settings
from jwkest.jwt import JWT


def parse_timestamp(timestamp):
    try:
        dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        dt = dateparser.parse(timestamp)
    return dt


@memoize(timeout=300)
def fetch_member_data(member, provider):
    '''Fetch FHIR data from HIXNY data provider (sharemyhealth)
    If data not available, returns None
    '''
    url = f"{settings.SOCIAL_AUTH_SHAREMYHEALTH_HOST}/hixny/api/fhir/stu3/Patient/$everything"
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
    prev_date = None
    prev_name = None
    for entry in data.get('entry', []):
        resource = entry['resource']
        if resource['resourceType'] in [
                'MedicationRequest',
                'MedicationStatement',
                'MedicationDispense',
        ]:
            name = resource['medicationReference']['display']
            date = resource.get('effectivePeriod', {}).get('start', None)

            # Combine records that have the same name, when the date is the same or null
            if (name and name == prev_name
                    and ((date and (date == prev_date)) or (not date and prev_date))):
                date = prev_date

            prev_date = date
            prev_name = name

            # build the id from the date and name
            id_hash = hashlib.new('sha256')
            id_hash.update((name + date).encode('utf-8'))
            id = base64.urlsafe_b64encode(id_hash.digest())

            prescriptions.setdefault(id, {'name': resource['medicationReference']['display']})

            if resource['resourceType'] == "MedicationRequest":
                prescriptions[id]['agent'] = resource.get('requester', {}).get('agent', {})
                prescriptions[id]['request_status'] = resource['status']
            elif resource['resourceType'] == "MedicationDispense":
                prescriptions[id]['dispense_status'] = resource['status']
            elif resource['resourceType'] == "MedicationStatement":
                prescriptions[id]['statement_status'] = resource['status']
                prescriptions[id]['effectivePeriod'] = {
                    key: parse_timestamp(value)
                    for key, value in resource.get('effectivePeriod', {}).items()
                }
                if 'dosage' in resource:
                    prescriptions[id]['dosage'] = {
                        k: v
                        for k, v in resource['dosage'][0]['doseQuantity'].items()
                        if k in ['value', 'unit']
                    }
                else:
                    prescriptions[id]['dosage'] = {}
                prescriptions[id]['taken'] = resource.get('taken', '')

    return prescriptions


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
