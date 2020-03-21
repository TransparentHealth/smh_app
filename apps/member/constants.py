RECORDS = [
    {'name': 'Diagnoses', 'slug': 'diagnoses'},
    {'name': 'Prescriptions', 'slug': 'prescriptions'},
    {'name': 'Allergies', 'slug': 'allergies'},
    {'name': 'Procedures', 'slug': 'procedures'},
    # {
    #   'name': 'ED Reports',
    #   'slug': 'ed-reports',
    # },
    # {
    #   'name': 'Family History',
    #   'slug': 'family-history',
    # },
    # {
    #   'name': 'Demographics',
    #   'slug': 'demographics',
    # },
    # {
    #   'name': 'Discharge Summaries',
    #   'slug': 'discharge-summaries',
    # },
    # {
    #   'name': 'Immunizations',
    #   'slug': 'immunizations',
    # },
    {'name': 'Lab Results', 'slug': 'lab-results'},
    # {
    #   'name': 'Progress Notes',
    #   'slug': 'progress-notes',
    # },
    {
      'name': 'Vital Signs',
      'slug': 'vital-signs',
    },
]

PROVIDER_RESOURCES = ['Location', 'Organization', 'Practitioner', 'PractitionerRole', 'CareTEam']

FIELD_TITLES = [
    {'profile': 'AllergyIntolerance',
     'elements': [
        {'system_name': 'id', 'show_name': 'Ref#'},
        {'system_name': 'clinicalStatus', 'show_name': 'Status'},
        {'system_name': 'verificationStatus', 'show_name': 'Verified'},
        {'system_name': 'onsetDateTime', 'show_name': 'Onset'},
        {'system_name': 'assertedDate', 'show_name': 'Asserted'},
        {'system_name': 'code', 'show_name': 'Info'},
        {'system_name': 'type', 'show_name': 'Severity'},
     ]},
    {'profile': 'medicationRequest',
     'elements': [
        {'system_name': 'dispenseRequest', 'show_name': 'Refills'},
     ]},
]

RECORDS_STU3 = [
    {'name': 'Account', 'slug': 'account', 'call_type': 'fhir', 'resources': ['Account'], 'display': 'Account', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ActivityDefinition', 'slug': 'activitydefinition', 'call_type': 'fhir', 'resources': ['ActivityDefinition'], 'display': 'Activity Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'AllergyIntolerance', 'slug': 'allergyintolerance', 'call_type': 'fhir', 'resources': ['AllergyIntolerance'],
     'display': 'Allergies',
     'headers': ['id', 'clinicalStatus', 'verificationStatus', 'category', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'patient'],
     'field_formats':[{"field": "category", "detail": "$.category[*]", "format": ""},
                     {"field": "code", "detail": "$.code.text", "format": ""},
                     {"field": "onsetDateTime", "detail": "$.onsetDateTime[*]", "format": {"start": 0, "end": 10}},
                     {"field": "assertedDate", "detail": "$.assertedDate[*]", "format": {"start": 0, "end": 10}}
                     ],
     'sort': ['-onsetDateTime']},
    {'name': 'AdverseEvent', 'slug': 'adverseevent', 'call_type': 'fhir', 'resources': ['AdverseEvent'], 'display': 'Adverse Event', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Appointment', 'slug': 'appointment', 'call_type': 'fhir', 'resources': ['Appointment'], 'display': 'Appointment', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'AppointmentResponse', 'slug': 'appointmentresponse', 'call_type': 'fhir', 'resources': ['AppointmentResponse'], 'display': 'Appointment Response', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'AuditEvent', 'slug': 'auditevent', 'call_type': 'fhir', 'resources': ['AuditEvent'], 'display': 'Audit Event', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Basic', 'slug': 'basic', 'call_type': 'fhir', 'resources': ['Basic'], 'display': 'Basic', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Binary', 'slug': 'binary', 'call_type': 'fhir', 'resources': ['Binary'], 'display': 'Binary', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'BodySite', 'slug': 'bodysite', 'call_type': 'fhir', 'resources': ['BodySite'], 'display': 'Body Site', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Bundle', 'slug': 'bundle', 'call_type': 'fhir', 'resources': ['Bundle'], 'display': 'Bundle', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'CapabilityStatement', 'slug': 'capabilitystatement', 'call_type': 'fhir', 'resources': ['CapabilityStatement'], 'display': 'Capability Statement', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'CarePlan', 'slug': 'careplan', 'call_type': 'fhir', 'resources': ['CarePlan'], 'display': 'Care Plan', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'CareTeam', 'slug': 'careteam', 'call_type': 'fhir', 'resources': ['CareTeam'], 'display': 'Care Team', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ChargeItem', 'slug': 'chargeitem', 'call_type': 'fhir', 'resources': ['ChargeItem'], 'display': 'Charge Item', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Claim', 'slug': 'claim', 'call_type': 'fhir', 'resources': ['Claim'], 'display': 'Claim', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ClaimResponse', 'slug': 'claimresponse', 'call_type': 'fhir', 'resources': ['ClaimResponse'], 'display': 'Claim Response', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ClinicalImpression', 'slug': 'clinicalimpression', 'call_type': 'fhir', 'resources': ['ClinicalImpression'], 'display': 'Clinical Impression', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'CodeSystem', 'slug': 'codesystem', 'call_type': 'fhir', 'resources': ['CodeSystem'], 'display': 'Code System', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Communication', 'slug': 'communication', 'call_type': 'fhir', 'resources': ['Communication'], 'display': 'Communication', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'CommunicationRequest', 'slug': 'communicationrequest', 'call_type': 'fhir', 'resources': ['CommunicationRequest'], 'display': 'Communication Response', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'CompartmentDefinition', 'slug': 'compartmentdefinition', 'call_type': 'fhir', 'resources': ['CompartmentDefinition'], 'display': 'Compartment Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Composition', 'slug': 'composition', 'call_type': 'fhir', 'resources': ['Composition'],
     'display': 'Composition',
     'headers': ['id', 'status', 'type', 'date', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'class', 'subject', 'author', 'title', 'attester', 'custodian', 'event'],
     'field_formats':[{'field': 'type', 'detail': '$.type.coding[*].display', 'format': ''},
                      {'field': 'date', 'detail': '$.date', 'format': {'start': 0, 'end': 10}},
                      {'field': 'section', 'detail': '$.section[*].entry[*].display', 'format': ''}],
     'sort': ['-date']
     },
    {'name': 'ConceptMap', 'slug': 'conceptmap', 'call_type': 'fhir', 'resources': ['ConceptMap'],
     'display': 'Concept Map',
     'headers': ['id', '*'],
     'exclude': ['meta', 'resourceType'],
     'field_formats':[],
     'sort': ['-id']
     },
    {'name': 'Condition', 'slug': 'condition', 'call_type': 'fhir', 'resources': ['Condition'],
     'display': 'Condition',
     'headers': ['id', 'clinicalStatus', 'verificationStatus', 'code'],
     'exclude': ['meta', 'resourceType', 'category', 'subject'],
     'field_formats': [{'field': 'code', 'detail': '$.code.text', 'format': ''}],
     'sort': ['-id']
     },
    {'name': 'Consent', 'slug': 'consent', 'call_type': 'fhir', 'resources': ['Consent'], 'display': 'Consent', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Contract', 'slug': 'contract', 'call_type': 'fhir', 'resources': ['Contract'], 'display': 'Contract', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Coverage', 'slug': 'coverage', 'call_type': 'fhir', 'resources': ['Coverage'], 'display': 'Coverage', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DataElement', 'slug': 'dataelement', 'call_type': 'fhir', 'resources': ['DataElement'], 'display': 'Data Element', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DetectedIssue', 'slug': 'detectedissue', 'call_type': 'fhir', 'resources': ['DetectedIssue'], 'display': 'Detected Issue', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Device', 'slug': 'device', 'call_type': 'fhir', 'resources': ['Device'], 'display': 'Device', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DeviceComponent', 'slug': 'devicecomponent', 'call_type': 'fhir', 'resources': ['DeviceComponent'], 'display': 'Device Component', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DeviceMetric', 'slug': 'devicemetric', 'call_type': 'fhir', 'resources': ['DeviceMetric'], 'display': 'Device Metric', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DeviceRequest', 'slug': 'devicerequest', 'call_type': 'fhir', 'resources': ['DeviceRequest'], 'display': 'Device Request', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DeviceUseStatement', 'slug': 'deviceusestatement', 'call_type': 'fhir', 'resources': ['DeviceUseStatement'], 'display': 'Device Use Statement', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DiagnosticReport', 'slug': 'diagnosticreport', 'call_type': 'fhir', 'resources': ['DiagnosticReport'],
     'display': 'Diagnostic Report',
     'headers': ['id', 'status', 'result', '*'],
     'exclude': ['resourceType', 'meta', 'identifier', 'subject'],
     'field_formats':[{"field": "result", "detail": "$.result[*].display", "format": ""},
                     {"field": "code", "detail": "$.code.coding[*].display", "format": ""},
                     {"field": "effectivePeriod", "detail": "$.effectivePeriod[*]", "format": {"start": 0, "end": 10}}],
     'sort': ['-effectivePeriod']
     },
    {'name': 'DocumentManifest', 'slug': 'documentmanifest', 'call_type': 'fhir', 'resources': ['DocumentManifest'], 'display': 'Document Manifest', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'DocumentReference', 'slug': 'documentreference', 'call_type': 'fhir', 'resources': ['DocumentReference'], 'display': 'Document Reference',
     'headers': ['id', 'status', 'type', 'indexed', '*'],
     'exclude': ['meta', 'identifier', 'resourceType'],
     'field_formats':[{'field': 'type', 'detail': '$.type.coding[*].display', 'format': ''},
                      {"field": "indexed", "detail": "$.indexed", "format": {"start": 0, "end": 10}}],
     'sort': ['-indexed']
     },
    {'name': 'EligibilityRequest', 'slug': 'eligibilityrequest', 'call_type': 'fhir', 'resources': ['EligibilityRequest'], 'display': 'Eligibility Request',
     'headers': ['id', 'status', '*'],
     'exclude': ['meta', 'identifier', 'resourceType']
     },
    {'name': 'EligibilityResponse', 'slug': 'eligibilityresponse', 'call_type': 'fhir', 'resources': ['EligibilityResponse'], 'display': 'Eligibility Response',
     'headers': ['id', '*'],
     'exclude': ['meta', 'identifier', 'resourceType']
     },
    {'name': 'Encounter', 'slug': 'encounter', 'call_type': 'fhir', 'resources': ['Encounter'], 'display': 'Encounter',
     'headers': ['id', 'status', 'type', 'period', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject'],
     'field_formats':[{'field': 'period', 'detail': '$.period.start', 'format': {'start': 0, 'end': 10}},
                      {"field": "location", "detail": "$.location[*].location.display", "format": ""},
                      {"field": "type", "detail": "$.type[*].text", "format": ""},
                      {"field": "participant", "detail": "$.participant[*].individual.display", "format": ""}],
     'sort': ['-period[0]',]
     },
    {'name': 'Endpoint', 'slug': 'endpoint', 'call_type': 'fhir', 'resources': ['Endpoint'], 'display': 'Endpoint', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'EnrollmentRequest', 'slug': 'enrollmentrequest', 'call_type': 'fhir', 'resources': ['EnrollmentRequest'], 'display': 'Enrollment Request', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'EnrollmentResponse', 'slug': 'enrollmentresponse', 'call_type': 'fhir', 'resources': ['EnrollmentResponse'], 'display': 'Enrollment Response', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'EpisodeOfCare', 'slug': 'episodeofcare', 'call_type': 'fhir', 'resources': ['EpisodeOfCare'], 'display': 'Episode Of Care', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ExpansionProfile', 'slug': 'expansionprofile', 'call_type': 'fhir', 'resources': ['ExpansionProfile'], 'display': 'Expansion Profile', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ExplanationOfBenefit', 'slug': 'explanationofbenefit', 'call_type': 'fhir', 'resources': ['ExplanationOfBenefit'], 'display': 'Explanation Of Benefit', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'FamilyMemberHistory', 'slug': 'familymemberhistory', 'call_type': 'fhir', 'resources': ['FamilyMemberHistory'], 'display': 'Family Member History', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Flag', 'slug': 'flag', 'call_type': 'fhir', 'resources': ['Flag'], 'display': 'Flag', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Goal', 'slug': 'goal', 'call_type': 'fhir', 'resources': ['Goal'], 'display': 'Goal', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'GraphDefinition', 'slug': 'graphdefinition', 'call_type': 'fhir', 'resources': ['GraphDefinition'], 'display': 'Graph Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Group', 'slug': 'group', 'call_type': 'fhir', 'resources': ['Group'], 'display': 'Group', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'GuidanceResponse', 'slug': 'guidanceresponse', 'call_type': 'fhir', 'resources': ['GuidanceResponse'], 'display': 'Guidance Response', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'HealthcareService', 'slug': 'healthcareservice', 'call_type': 'fhir', 'resources': ['HealthcareService'], 'display': 'Healthcare Service', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ImagingManifest', 'slug': 'imagingmanifest', 'call_type': 'fhir', 'resources': ['ImagingManifest'], 'display': 'Imaging Manifest', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ImagingStudy', 'slug': 'imagingstudy', 'call_type': 'fhir', 'resources': ['ImagingStudy'], 'display': 'Imaging Study', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Immunization', 'slug': 'immunization', 'call_type': 'fhir', 'resources': ['Immunization'], 'display': 'Immunization', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ImmunizationRecommendation', 'slug': 'immunizationrecommendation', 'call_type': 'fhir', 'resources': ['ImmunizationRecommendation'], 'display': 'Immunization Recommendation', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ImplementationGuide', 'slug': 'implementationguide', 'call_type': 'fhir', 'resources': ['ImplementationGuide'], 'display': 'Implementation Guide', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Library', 'slug': 'library', 'call_type': 'fhir', 'resources': ['Library'], 'display': 'Library', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Linkage', 'slug': 'linkage', 'call_type': 'fhir', 'resources': ['Linkage'], 'display': 'Linkage', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'List', 'slug': 'list', 'call_type': 'fhir', 'resources': ['List'], 'display': 'List', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Location', 'slug': 'location', 'call_type': 'fhir', 'resources': ['Location'], 'display': 'Location',
     'headers': ['id', 'name', '*'],
     'exclude': ['meta', 'identifier', 'resourceType'],
     'field_formats': [],
     'sort': ['name']
     },
    {'name': 'Measure', 'slug': 'measure', 'call_type': 'fhir', 'resources': ['Measure'], 'display': 'Measure', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'MeasureReport', 'slug': 'measurereport', 'call_type': 'fhir', 'resources': ['MeasureReport'], 'display': 'Measure Report', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Media', 'slug': 'media', 'call_type': 'fhir', 'resources': ['Media'], 'display': 'Media', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Medication', 'slug': 'medication', 'call_type': 'fhir', 'resources': ['Medication'], 'display': 'Medication',
     'headers': ['id', 'code'],
     'exclude': ['meta', 'resourceType'],
     'field_formats':[{"field": "code", "detail": "$.code.coding[*].display", "format": ''}],
     'sort': []
     },
    {'name': 'MedicationAdministration', 'slug': 'medicationadministration', 'call_type': 'fhir', 'resources': ['MedicationAdministration'], 'display': 'Medication Administration', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'MedicationDispense', 'slug': 'medicationdispense', 'call_type': 'fhir', 'resources': ['MedicationDispense'], 'display': 'Medication Dispense',
     'headers': ['id', 'status', 'medicationReference', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject'],
     'field_formats': [
                       {'field': 'medicationReference', 'detail': '$.medicationReference.display', 'format': ''},
     ],
     'sort': ['name']
     },
    {'name': 'MedicationRequest', 'slug': 'medicationrequest', 'call_type': 'fhir', 'resources': ['MedicationRequest'], 'display': 'Medication Request',
     'headers': ['id', 'status', 'intent', 'medicationReference', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject'],
     'field_formats': [{'field': 'medicationReference', 'detail': '$.medicationReference.display', 'format': ''},
                       {'field': 'requester', 'detail': '$.requester.agent.display', 'format': ''},
                       {'field': 'dispenseRequest', 'detail': '$.dispenseRequest.numberOfRepeatsAllowed', 'format': ''}
      ],
     'sort': []
     },
    {'name': 'MedicationStatement', 'slug': 'medicationstatement', 'call_type': 'fhir', 'resources': ['MedicationStatement'], 'display': 'Medication Statement',
     'headers': ['id', 'status', 'medicationReference', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject', 'taken'],
     'field_formats': [
         {'field': 'medicationReference', 'detail': '$.medicationReference.display', 'format': ''},
         {'field': 'effectivePeriod', 'detail': '$.effectivePeriod[*]', 'format': {'start': 0, 'end': 10}},
         {'field': 'informationSource', 'detail': '$.informationSource.display', 'format': ''},
         {'field': 'dosage', 'detail': '$.dosage[*].doseQuantity', 'format': ''},
     ],
     'sort': ['name']

     },
    {'name': 'MessageDefinition', 'slug': 'messagedefinition', 'call_type': 'fhir', 'resources': ['MessageDefinition'], 'display': 'Message Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'MessageHeader', 'slug': 'messageheader', 'call_type': 'fhir', 'resources': ['MessageHeader'], 'display': 'Message Header', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'NamingSystem', 'slug': 'namingsystem', 'call_type': 'fhir', 'resources': ['NamingSystem'], 'display': 'Naming System', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'NutritionOrder', 'slug': 'nutritionorder', 'call_type': 'fhir', 'resources': ['NutritionOrder'], 'display': 'Nutrition Order', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    # Observation mixes labs and vital-signs
    {'name': 'Observation', 'slug': 'observation', 'call_type': 'fhir', 'resources': ['Observation'], 'display': 'Observation',
     'headers': ['id', 'status', 'code', 'effectivePeriod', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject'],
     'field_formats':[{"field": "code", "detail": "$.code.coding[*].display", "format": ''},
                      {'field': 'effectivePeriod', 'detail': '$.effectivePeriod[*]', 'format': {'start': 0, 'end': 10}},
                      ],
     'sort': []
     },
    # Split to vital-signs
    {'name': 'VitalSigns', 'slug': 'vitalsigns', 'call_type': 'custom', 'resources': ['Observation'], 'display': 'Vital Signs',
     'headers': ['id', 'status', 'code', 'effectivePeriod', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject'],
     'field_formats':[{"field": "code", "detail": "$.code.coding[*].display", "format": ''},
                      {'field': 'effectivePeriod', 'detail': '$.effectivePeriod[*]', 'format': {'start': 0, 'end': 10}},
                      ],
     'sort': []
     },
    # Split to Lab Results
    {'name': 'LabResults', 'slug': 'labresults', 'call_type': 'custom', 'resources': ['Observation'], 'display': 'Lab Results',
     'headers': ['id', 'status', 'code', 'effectivePeriod', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject'],
     'field_formats':[{"field": "code", "detail": "$.code.coding[*].display", "format": ''},
                      {'field': 'effectivePeriod', 'detail': '$.effectivePeriod[*]', 'format': {'start': 0, 'end': 10}},
                      ],
     'sort': []
     },
    #
    {'name': 'OperationDefinition', 'slug': 'operationdefinition', 'call_type': 'fhir', 'resources': ['OperationDefinition'], 'display': 'Operation Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'OperationOutcome', 'slug': 'operationoutcome', 'call_type': 'fhir', 'resources': ['OperationOutcome'], 'display': 'Operation Outcome', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Organization', 'slug': 'organization', 'call_type': 'fhir', 'resources': ['Organization'], 'display': 'Organization',
     'headers': ['id', 'name', 'telecom', 'address', '*'],
     'exclude': ['meta', 'identifier', 'resourceType'],
     'field_formats': [{"field": "telecom", "detail": "$.telecom[*].value", "format": ''},
                       {"field": "address", "detail": "$.address[*]", "format": ''}
                       ],
     'sort': ['name',]
     },
    {'name': 'Parameters', 'slug': 'parameters', 'call_type': 'fhir', 'resources': ['Parameters'], 'display': 'Parameters', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Patient', 'slug': 'patient', 'call_type': 'fhir', 'resources': ['Patient'], 'display': 'Patient',
     'headers': ['id', 'name', 'telecom', 'gender', 'birthDate', '*'],
     'exclude': ['meta', 'identifier', 'resourceType'],
     'field_formats':[{'field': 'birthDate', 'detail': '$.birthDate', 'format': {'start': 0, 'end': 10}},
                      {'field': 'communication', 'detail': '$.communication[*].language.coding[*].code', 'format': ''}
                      ],
     'sort': []
     },
    {'name': 'PaymentNotice', 'slug': 'paymentnotice', 'call_type': 'fhir', 'resources': ['PaymentNotice'], 'display': 'Payment Notice', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'PaymentReconciliation', 'slug': 'paymentreconciliation', 'call_type': 'fhir', 'resources': ['PaymentReconciliation'], 'display': 'Payment Reconciliation', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Person', 'slug': 'person', 'call_type': 'fhir', 'resources': ['Person'], 'display': 'Person', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'PlanDefinition', 'slug': 'plandefinition', 'call_type': 'fhir', 'resources': ['PlanDefinition'], 'display': 'Plan Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Practitioner', 'slug': 'practitioner', 'call_type': 'fhir', 'resources': ['Practitioner'], 'display': 'Provider',
     'headers': ['id', 'practitioner', 'organization', '*'],
     'exclude': ['meta', 'identifier', 'resourceType'],
     'field_formats': [{"field": "practitioner", "detail": "$.practitioner.display", "format": ''},
                      ],
    'sort': ['practitioner']
     },
    {'name': 'PractitionerRole', 'slug': 'practitionerrole', 'call_type': 'fhir', 'resources': ['PractitionerRole'], 'display': 'Practitioner Role',
     'headers': ['id', 'practitioner', 'organization', '*'],
     'exclude': ['meta', 'identifier', 'resourceType'],
     'field_formats': [{"field": "practitioner", "detail": "$.practitioner.display", "format": ''},
                       {"field": "organization", "detail": "$.organization.display", "format": ''},
                       ],
     'sort': ['practitioner']
     },
    {'name': 'Procedure', 'slug': 'procedure', 'call_type': 'fhir', 'resources': ['Procedure'], 'display': 'Procedure',
     'headers': ['id', 'status', 'code', '*'],
     'exclude': ['meta', 'identifier', 'resourceType', 'subject'],
     'field_formats': [{"field": "code", "detail": "$.code.coding[*].display", "format": ''},
                       {'field': 'performedPeriod', 'detail': '$.performedPeriod[*]', 'format': {'start': 0, 'end': 10}},
                       ],
     'sort': []
     },
    {'name': 'ProcedureRequest', 'slug': 'procedurerequest', 'call_type': 'fhir', 'resources': ['ProcedureRequest'], 'display': 'Procedure Request', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ProcessRequest', 'slug': 'processrequest', 'call_type': 'fhir', 'resources': ['ProcessRequest'], 'display': 'Process Request', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ProcessResponse', 'slug': 'processresponse', 'call_type': 'fhir', 'resources': ['ProcessResponse'], 'display': 'Process Response', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Provenance', 'slug': 'provenance', 'call_type': 'fhir', 'resources': ['Provenance'], 'display': 'Provenance',
     'headers': ['id', 'recorded', '*'],
     'exclude': ['meta', 'resourceType', 'target', 'agent'],
     'field_formats': [{"field": "entity", "detail": "$.entity[*].whatReference.display", "format": ''},
                       {"field": "recorded", "detail": "$.recorded", 'format': {'start': 0, 'end': 10}}
                       ],
     'sort': ['-recorded']
     },
    {'name': 'Questionnaire', 'slug': 'questionnaire', 'call_type': 'fhir', 'resources': ['Questionnaire'], 'display': 'Questionnaire', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'QuestionnaireResponse', 'slug': 'questionnaireresponse', 'call_type': 'fhir', 'resources': ['QuestionnaireResponse'], 'display': 'Questionnaire Response', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ReferralRequest', 'slug': 'referralrequest', 'call_type': 'fhir', 'resources': ['ReferralRequest'], 'display': 'Referral Request', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'RelatedPerson', 'slug': 'relatedperson', 'call_type': 'fhir', 'resources': ['RelatedPerson'], 'display': 'Related Person', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'RequestGroup', 'slug': 'requestgroup', 'call_type': 'fhir', 'resources': ['RequestGroup'], 'display': 'Request Group', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ResearchStudy', 'slug': 'researchstudy', 'call_type': 'fhir', 'resources': ['ResearchStudy'], 'display': 'Research Study', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ResearchSubject', 'slug': 'researchsubject', 'call_type': 'fhir', 'resources': ['ResearchSubject'], 'display': 'Research Subject', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'RiskAssessment', 'slug': 'riskassessment', 'call_type': 'fhir', 'resources': ['RiskAssessment'], 'display': 'Risk Assessment', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Schedule', 'slug': 'schedule', 'call_type': 'fhir', 'resources': ['Schedule'], 'display': 'Schedule', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'SearchParameter', 'slug': 'searchparameter', 'call_type': 'fhir', 'resources': ['SearchParameter'], 'display': 'Search Parameter', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Sequence', 'slug': 'sequence', 'call_type': 'fhir', 'resources': ['Sequence'], 'display': 'Sequence', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ServiceDefinition', 'slug': 'servicedefinition', 'call_type': 'fhir', 'resources': ['ServiceDefinition'], 'display': 'Service Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Slot', 'slug': 'slot', 'call_type': 'fhir', 'resources': ['Slot'], 'display': 'Slot', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Specimen', 'slug': 'specimen', 'call_type': 'fhir', 'resources': ['Specimen'], 'display': 'Specimen', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'StructureDefinition', 'slug': 'structuredefinition', 'call_type': 'fhir', 'resources': ['StructureDefinition'], 'display': 'Structure Definition', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'StructureMap', 'slug': 'structuremap', 'call_type': 'fhir', 'resources': ['StructureMap'], 'display': 'Structure Map', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Subscription', 'slug': 'subscription', 'call_type': 'fhir', 'resources': ['Subscription'], 'display': 'Subscription', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Substance', 'slug': 'substance', 'call_type': 'fhir', 'resources': ['Substance'], 'display': 'Substance', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'SupplyDelivery', 'slug': 'supplydelivery', 'call_type': 'fhir', 'resources': ['SupplyDelivery'], 'display': 'Supply Delivery', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'SupplyRequest', 'slug': 'supplyrequest', 'call_type': 'fhir', 'resources': ['SupplyRequest'], 'display': 'Supply Request', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'Task', 'slug': 'task', 'call_type': 'fhir', 'resources': ['Task'], 'display': 'Task', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'TestScript', 'slug': 'testscript', 'call_type': 'fhir', 'resources': ['TestScript'], 'display': 'Test Script', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'TestReport', 'slug': 'testreport', 'call_type': 'fhir', 'resources': ['TestReport'], 'display': 'Test Report', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'ValueSet', 'slug': 'valueset', 'call_type': 'fhir', 'resources': ['ValueSet'], 'display': 'Value Set', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']},
    {'name': 'VisionPrescription', 'slug': 'visionprescription', 'call_type': 'fhir', 'resources': ['VisionPrescription'], 'display': 'Vision Prescription', 'headers': ['id', '*'], 'exclude': ['meta', 'identifier', 'resourceType']}
]
