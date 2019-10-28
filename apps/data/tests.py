import json
import logging
import os
from glob import glob

from django.test import TestCase

from apps.data.models.allergy import AllergyIntolerance
from apps.data.models.condition import Condition
from apps.data.models.encounter import Encounter
from apps.data.models.medication import (
    Medication,
    MedicationRequest,
    MedicationStatement,
)
from apps.data.models.observation import Observation
from apps.data.models.practitioner import Practitioner
from apps.data.models.procedure import Procedure

PATH = os.path.dirname(os.path.abspath(__file__))
DATA_MODELS = {
    'Observation': Observation,
    'Procedure': Procedure,
    'Medication': Medication,
    'MedicationRequest': MedicationRequest,
    'MedicationStatement': MedicationStatement,
    'Practitioner': Practitioner,
    'Condition': Condition,
    'Encounter': Encounter,
    'AllergyIntolerance': AllergyIntolerance,
}

logger = logging.getLogger(__name__)


class TestDataTestCase(TestCase):
    def test_validate_testdata(self):
        """testdata should validate against the data models."""
        filenames = glob(os.path.join(PATH, '..', '*.json'))
        errors = {}
        for filename in filenames:
            data = json.load(open(filename, 'rb'))
            for resource_entry in (entry['resource'] for entry in data['entry']):
                if resource_entry['resourceType'] in DATA_MODELS:
                    resource = DATA_MODELS[resource_entry['resourceType']].from_data(
                        resource_entry
                    )
                    if not resource.is_valid():
                        errors.setdefault(resource['resourceType'], [])
                        error = {
                            'filename': os.path.relpath(PATH, filename),
                            'id': resource['id'],
                            'errors': resource.errors,
                        }
                        logger.debug(error)
                        errors[resource['resourceType']].append(error)

        if errors:
            logger.debug(
                json.dumps(
                    {key: f"{len(val)} errors" for key, val in errors.items()}, indent=2
                )
            )
            raise ValueError('testdata did not validate.')
