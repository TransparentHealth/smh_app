import logging
from time import time
from memoize import memoize
import requests
from django.conf import settings
from jwkest.jwt import JWT

from apps.data.models.allergy import AllergyIntolerance
from apps.data.models.medication import (
    Medication,
    MedicationRequest,
    MedicationStatement,
)
from apps.data.models.practitioner import Practitioner

log = logging.getLogger(__name__)


@memoize(timeout=300)
def fetch_member_data(member, provider):
    '''Fetch FHIR data from HIXNY data provider (sharemyhealth)
    If data not available, returns None
    '''
    url = f"{settings.SOCIAL_AUTH_SHAREMYHEALTH_HOST}/hixny/api/fhir/stu3/Patient/$everything"
    social_auth = member.user.social_auth.filter(provider=provider).first()
    if social_auth is not None:
        access_token = social_auth.extra_data.get('access_token')
        if access_token is not None:
            r = requests.get(url, headers={'Authorization': 'Bearer %s' % access_token})
            if r.status_code == 403:
                refreshed = refresh_access_token(social_auth)
                if refreshed:  # repeat the previous request
                    access_token = social_auth.extra_data.get('access_token')
                    r = requests.get(url, headers={'Authorization': 'Bearer %s' % access_token})
            if r.status_code == 200:
                return r.json()
            else:
                return {
                    'error': 'Could not access member data: Status = %d' % r.status_code,
                    'responses': [r.text],
                }
    # fallback: empty member data
    return {'entry': []}


def refresh_access_token(social_auth):
    log.debug(f'refresh_access_token() {social_auth.user} {social_auth.provider}')
    if 'refresh_token' in social_auth.extra_data:
        if social_auth.provider == 'sharemyhealth': 
            refresh_url = f"{settings.SOCIAL_AUTH_SHAREMYHEALTH_HOST}/o/token/"
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': social_auth.extra_data['refresh_token'],
                'client_id': settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY,
                'client_secret': settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET,
            }
        elif social_auth.provider == 'vmi':
            refresh_url = f"{settings.SOCIAL_AUTH_VMI_HOST}/o/token/"
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': social_auth.extra_data['refresh_token'],
                'client_id': settings.SOCIAL_AUTH_VMI_KEY,
                'client_secret': settings.SOCIAL_AUTH_VMI_SECRET,
            }
        else:
            return

        refresh_response = requests.post(refresh_url, data=refresh_data)
        if refresh_response.status_code == 200:
            log.debug(f"refreshed=True {refresh_response.json()}")
            social_auth.extra_data.update(
                auth_time=time(),
                **{
                    k: v
                    for k, v in refresh_response.json().items()
                    if k in ['access_token', 'refresh_token', 'expires_in']
                },
            )
            social_auth.save()
            return True


def get_resource_data(data, resource_type, constructor=dict, id=None):
    return [
        constructor(item['resource'])
        for item in data.get('entry', [])
        if item['resource']['resourceType'] == resource_type
        if id is None or item['resource'].get('id') == id
    ]


def get_prescriptions(data, id=None, incl_practitioners=False, json=False):
    """Returns an medication-name-keyed dict of all prescriptions in the (FHIR) medical data.
    A Prescription consists of a MedicationRequest, along with a corresponding MedicationStatement,
    which are tied to a particular Medication.code.text (its name).
    Optionally filter the results on a given (Medication) id.
    Optionally include practitioners data in each prescription (for details rendering).
    """
    prescriptions = {
        # medication.code.text = the name of the medication
        medication.code.text: {
            'medication': medication,
            'requests': [],
            'statements': [],
        }
        for medication in get_resource_data(data, 'Medication', Medication.from_data)
        if id is None or medication.id == id
    }
    # organize all MedicationRequests & MedicationStatements by
    # Medication.code.text (its name)
    for med_req in get_resource_data(data, 'MedicationRequest', MedicationRequest.from_data):
        name = med_req.medicationReference.display
        if (name in prescriptions and med_req.requester and med_req.requester.agent.display not in [
                mr.requester.agent.display for mr in prescriptions[name]['requests'] if mr.requester
        ]):
            prescriptions[name]['requests'].append(med_req)
    # filter out prescriptions with no MedicationRequests
    for name in list(prescriptions.keys()):
        if not prescriptions[name]['requests']:
            del prescriptions[name]

    # add MedicationStatements
    for med_stmt in get_resource_data(data, 'MedicationStatement', MedicationStatement.from_data):
        name = med_stmt.medicationReference.display
        # only add non-duplicate MedicationStatements (based on its __str__
        # representation)
        if name in prescriptions and str(med_stmt) not in (
                str(ms) for ms in prescriptions[name]['statements']):
            prescriptions[name]['statements'].append(med_stmt)

    # sort MedicationStatements in effectiveDate.start descending order
    for name in prescriptions:
        prescriptions[name]['statements'] = sorted(
            prescriptions[name]['statements'],
            key=lambda statement: statement.effectivePeriod.start,
            reverse=True,
        )

    # include practitioners if requested, on each prescription -- keyed to
    # their id
    if incl_practitioners:
        practitioners = get_resource_data(data, 'Practitioner', Practitioner.from_data)
        for name in prescriptions:
            agent_ids = [
                request.requester.agent.id
                for request in prescriptions[name]['requests']
                if request.requester
            ]
            prescriptions[name]['practitioners'] = {
                practitioner.id: practitioner.dict()
                for practitioner in practitioners
                if practitioner.id in agent_ids
            }

    # render dicts if we're going to be converting to JSON
    if json:
        for name in prescriptions:
            prescriptions[name]['medication'] = prescriptions[name]['medication'].dict()
            prescriptions[name]['requests'] = [
                request.dict() for request in prescriptions[name]['requests']
            ]
            prescriptions[name]['statements'] = [
                request.dict() for request in prescriptions[name]['statements']
            ]

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
