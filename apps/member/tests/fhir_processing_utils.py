from django.test import TestCase
# from django.test.client import Client
# from django.urls import reverse
from ..constants import RECORDS_STU3
from ..fhir_utils import find_list_entry, filter_list
from ..fhir_requests import get_converted_fhir_resource


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


class ManipulateListTests(TestCase):
    # Testing filter list on include/exclude

    def test_filter_list_good_exclude_no_wildcard(self):
        f_list = ['a', 'b', 'c', 'd']
        incld = ['a', 'c']
        excld = ['b']

        good_result = ['a', 'c', 'd']
        result_list = filter_list(f_list, incld, excld)
        self.assertEqual(good_result, result_list)

    def test_filter_list_good_exclude_with_wildcard(self):
        f_list = ['a', 'b', 'c', 'd']
        incld = ['a', '*']
        excld = ['b']

        good_result = ['a', 'c', 'd']
        result_list = filter_list(f_list, incld, excld)
        self.assertEqual(good_result, result_list)

    def test_filter_list_bad_exclude_no_wildcard(self):
        f_list = ['a', 'b', 'c', 'd']
        incld = ['a', 'c']
        excld = ['b', 'e']

        good_result = ['a', 'c', 'd']
        result_list = filter_list(f_list, incld, excld)
        self.assertEqual(good_result, result_list)

    def test_filter_list_bad_exclude_wildcard(self):
        f_list = ['a', 'b', 'c', 'd']
        incld = ['a', '*']
        excld = ['e']

        good_result = ['a', 'b', 'c', 'd']
        result_list = filter_list(f_list, incld, excld)
        self.assertEqual(good_result, result_list)

    def test_filter_list_bad_include_no_wildcard(self):
        f_list = ['a', 'b', 'c', 'd']
        incld = ['e', 'c']
        excld = ['b']

        good_result = ['c']
        result_list = filter_list(f_list, incld, excld)
        self.assertEqual(good_result, result_list)

    def test_filter_list_bad_exclude_wildcard(self):
        f_list = ['a', 'b', 'c', 'd']
        incld = ['e', '*']
        excld = ['b']

        good_result = ['a', 'c', 'd']
        result_list = filter_list(f_list, incld, excld)
        self.assertEqual(good_result, result_list)
