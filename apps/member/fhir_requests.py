import logging
from django.conf import settings
logger = logging.getLogger(__name__)


BUNDLE = {"resourceType": "Bundle", "entry": []}

RESOURCES = ['Account', 'ActivityDefinition', 'AllergyIntolerance', 'AdverseEvent', 'Appointment',
             'AppointmentResponse', 'AuditEvent', 'Basic', 'Binary', 'BodySite', 'Bundle',
             'CapabilityStatement', 'CarePlan', 'CareTeam', 'ChargeItem', 'Claim', 'ClaimResponse',
             'ClinicalImpression', 'CodeSystem', 'Communication', 'CommunicationRequest',
             'CompartmentDefinition', 'Composition', 'ConceptMap', 'Condition', 'Consent',
             'Contract', 'Coverage', 'DataElement', 'DetectedIssue', 'Device', 'DeviceComponent',
             'DeviceMetric', 'DeviceRequest', 'DeviceUseStatement', 'DiagnosticReport', 'DocumentManifest',
             'DocumentReference', 'EligibilityRequest', 'EligibilityResponse', 'Encounter', 'Endpoint',
             'EnrollmentRequest', 'EnrollmentResponse', 'EpisodeOfCare', 'ExpansionProfile',
             'ExplanationOfBenefit', 'FamilyMemberHistory', 'Flag', 'Goal', 'GraphDefinition',
             'Group', 'GuidanceResponse', 'HealthcareService', 'ImagingManifest', 'ImagingStudy',
             'Immunization', 'ImmunizationRecommendation', 'ImplementationGuide', 'Library', 'Linkage',
             'List', 'Location', 'Measure', 'MeasureReport', 'Media',
             'Medication', 'MedicationAdministration', 'MedicationDispense', 'MedicationRequest',
             'MedicationStatement', 'MessageDefinition', 'MessageHeader', 'NamingSystem',
             'NutritionOrder', 'Observation', 'OperationDefinition', 'OperationOutcome',
             'Organization', 'Parameters', 'Patient', 'PaymentNotice', 'PaymentReconciliation',
             'Person', 'PlanDefinition', 'Practitioner', 'PractitionerRole', 'Procedure',
             'ProcedureRequest', 'ProcessRequest', 'ProcessResponse', 'Provenance',
             'Questionnaire', 'QuestionnaireResponse', 'ReferralRequest', 'RelatedPerson',
             'RequestGroup', 'ResearchStudy', 'ResearchSubject', 'RiskAssessment',
             'Schedule', 'SearchParameter', 'Sequence', 'ServiceDefinition', 'Slot', 'Specimen',
             'StructureDefinition', 'StructureMap', 'Subscription', 'Substance', 'SupplyDelivery',
             'SupplyRequest', 'Task', 'TestScript', 'TestReport', 'ValueSet', 'VisionPrescription']

VITALSIGNS = ['3141-9', '8302-2', '39156-5',
              '8480-6', '8462-4', '8867-4', '8310-5', '9279-1']

# True or False to enable debug printing
DEBUG_MODULE = False


def get_converted_fhir_resource(fhir_data, resourcetype="all"):
    """
    Get resourceType using HIE_Profile.fhir_content as fhir_data
    :param fhir_data: source fhir bundle
    :param resourcetype:
    :return:

    """
    # print(resourceType)
    resource_list = []
    if isinstance(resourcetype, str):
        if resourcetype.lower() == "all":
            resource_list = RESOURCES
        else:
            resource_list = [resourcetype]
    else:
        for r in resourcetype:
            if r in RESOURCES:
                resource_list.append(r)

    # print("Getting %s" % resource_list)

    bundle = {"resourceType": "Bundle", "entry": []}

    fd = get_resource_data(fhir_data, resource_list)
    # print("Got %s records for %s" % (len(fd), resource_list))
    if len(fd) > 0:
        for i in fd:
            # print("adding %s" % i)
            bundle["entry"].append(i)
    # print(len(bundle['entry']))

    return bundle


def get_resource_data(data, resource_types, constructor=dict, id=None):
    if isinstance(resource_types, str):
        resource_types = [resource_types]
    return [
        constructor(item['resource'])
        for item in (data or {}).get('entry', [])
        if item['resource']['resourceType'] in resource_types
        if id is None or item['resource'].get('id') == id
    ]


def get_vital_signs(fhir_data, record):
    """
    get vital-signs from observations

    param fhir_data:
    :return:
    """

    bundle = {"resourceType": "Bundle", "entry": []}

    o_bundle = get_converted_fhir_resource(fhir_data,
                                           record['resources'])

    if len(o_bundle["entry"]) == 0:
        return bundle
    else:
        observations = o_bundle['entry']


    found = 0
    skipped = 0
    for o in observations:

        if o["code"]["coding"][0]["code"] in VITALSIGNS:
            # print("adding...")
            bundle["entry"].append(o)
            found += 1
        else:
            # print("skipping,,,,,")
            skipped += 1

    if DEBUG_MODULE:
        print("Vital Signs: Skipped:%s Added: %s of %s and returning %s" % (skipped,
                                                                            found,
                                                                            len(observations),
                                                                            len(bundle['entry'])))
    return bundle


def get_lab_results(fhir_data, record):
    """
    get lab results by excluding vital-signs from observations
    :param fhir_data:
    :return:
    """

    bundle = {"resourceType": "Bundle", "entry": []}

    # print("base bundle:", len(bundle['entry']))
    o_bundle = get_converted_fhir_resource(fhir_data,
                                           record['resources'])

    if len(o_bundle["entry"]) == 0:
        return bundle
    else:
        # print("how big", len(o_bundle['entry']))
        observations = o_bundle['entry']

    found = 0
    skipped = 0
    # print("Lab Results:Bundle size:", len(bundle['entry']))
    for o in o_bundle['entry']:
        # print(o["code"]["coding"][0]["code"], VITALSIGNS)
        if o['code']['coding'][0]['code'] in VITALSIGNS:
            # print("skipping...")
            skipped += 1
            # print("skipped Bundle size:", skipped, "/", len(bundle['entry']))

        else:
            # print("adding...")
            bundle['entry'].append(o)
            found += 1
            # print("added Bundle size:", len(bundle['entry']))


    if DEBUG_MODULE:
        print("Lab Results: Skipped:%s Added: %s of %s and returning %s" % (skipped,
                                                                            found,
                                                                            len(observations),
                                                                            len(bundle['entry'])))

    return bundle
