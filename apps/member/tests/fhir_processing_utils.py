from django.test import TestCase
# from django.test.client import Client
# from django.urls import reverse
from ..constants import RECORDS_STU3
from ..fhir_utils import find_list_entry
from ..fhir_requests import get_converted_fhir_resource
import json


class ExtractFromFHIRTests(TestCase):
    # Testing extract from a FHIR bundle

    def setup(self):
        # do any prep activities
        # load the json file in to data
        patch_file = './big_ccda_fhir_bundle.json'
        f = open(patch_file, 'r')
        self.fhir_data = json.load(f)

    def test_get_resource_from_fhir(self):
        """
        Get a resource and extract from fhir bundle

        """
        # get Observation resources
        resource = find_list_entry(RECORDS_STU3, 'name', 'Observation')

        selected_resources = get_converted_fhir_resource(self.fhir_data, [resource['name'], ])
        print("getting Observations")
        self.assertEqual(len(selected_resources), 290)
