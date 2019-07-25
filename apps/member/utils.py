import hashlib
import base64

from memoize import memoize
import requests
from django.conf import settings
from jwkest.jwt import JWT

from apps.data.models.allergy import AllergyIntolerance
from apps.data.models.medication import Medication, MedicationRequest, MedicationStatement
from apps.data.util import parse_timestamp


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


def get_resource_data(data, resource_type, constructor=dict):
    return [
        constructor(item['resource'])
        for item in data.get('entry', [])
        if item['resource']['resourceType'] == resource_type
    ]


def get_prescriptions(data):
    """Returns an medication-name-keyed dict of all prescriptions in the (FHIR) medical data.
    A Prescription consists of a MedicationRequest, along with a corresponding MedicationStatement,
    which are tied to a particular Medication.code.text (its name)
    """
    prescriptions = {
        # medication.code.text = the name of the medication
        medication.code.text: {'medication': medication, 'requests': [], 'statements': []}
        for medication in get_resource_data(data, 'Medication', Medication.from_data)
    }
    # organize all MedicationRequests & MedicationStatements by Medication.code.text (its name)
    for med_req in get_resource_data(data, 'MedicationRequest', MedicationRequest.from_data):
        name = med_req.medicationReference.display
        if med_req.requester and med_req.requester.agent.display not in [
            mr.requester.agent.display for mr in prescriptions[name]['requests'] if mr.requester
        ]:
            prescriptions[name]['requests'].append(med_req)
    for med_stmt in get_resource_data(data, 'MedicationStatement', MedicationStatement.from_data):
        name = med_stmt.medicationReference.display
        # filter out duplicate MedicationStatements (based on its __str__ representation)
        if str(med_stmt) not in (str(ms) for ms in prescriptions[name]['statements']):
            prescriptions[name]['statements'].append(med_stmt)
    for name in list(prescriptions.keys()):
        # filter out prescriptions with no MedicationRequests
        if not prescriptions[name]['requests']:
            del prescriptions[name]
        if name in prescriptions:
            # sort MedicationStatements in effectiveDate.start descending order
            prescriptions[name]['statements'] = sorted(
                prescriptions[name]['statements'],
                key=lambda statement: statement.effectivePeriod.start,
                reverse=True,
            )
    return prescriptions


def get_allergies(data, keys=None):
    return [
        AllergyIntolerance.from_data(entry['resource'], keys=keys)
        for entry in data.get('entry', [])
        if entry['resource']['resourceType'] == 'AllergyIntolerance'
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
