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

RECORDS_STU3 = [
    {'name': 'Account', 'slug': 'account', 'call_type': 'fhir', 'resources': ['Account']},
    {'name': 'ActivityDefinition', 'slug': 'activitydefinition', 'call_type': 'fhir', 'resources': ['ActivityDefinition']},
    {'name': 'AllergyIntolerance', 'slug': 'allergyintolerance', 'call_type': 'fhir', 'resources': ['AllergyIntolerance']},
    {'name': 'AdverseEvent', 'slug': 'adverseevent', 'call_type': 'fhir', 'resources': ['AdverseEvent']},
    {'name': 'Appointment', 'slug': 'appointment', 'call_type': 'fhir', 'resources': ['Appointment']},
    {'name': 'AppointmentResponse', 'slug': 'appointmentresponse', 'call_type': 'fhir', 'resources': ['AppointmentResponse']},
    {'name': 'AuditEvent', 'slug': 'auditevent', 'call_type': 'fhir', 'resources': ['AuditEvent']},
    {'name': 'Basic', 'slug': 'basic', 'call_type': 'fhir', 'resources': ['Basic']},
    {'name': 'Binary', 'slug': 'binary', 'call_type': 'fhir', 'resources': ['Binary']},
    {'name': 'BodySite', 'slug': 'bodysite', 'call_type': 'fhir', 'resources': ['BodySite']},
    {'name': 'Bundle', 'slug': 'bundle', 'call_type': 'fhir', 'resources': ['Bundle']},
    {'name': 'CapabilityStatement', 'slug': 'capabilitystatement', 'call_type': 'fhir', 'resources': ['CapabilityStatement']},
    {'name': 'CarePlan', 'slug': 'careplan', 'call_type': 'fhir', 'resources': ['CarePlan']},
    {'name': 'CareTeam', 'slug': 'careteam', 'call_type': 'fhir', 'resources': ['CareTeam']},
    {'name': 'ChargeItem', 'slug': 'chargeitem', 'call_type': 'fhir', 'resources': ['ChargeItem']},
    {'name': 'Claim', 'slug': 'claim', 'call_type': 'fhir', 'resources': ['Claim']},
    {'name': 'ClaimResponse', 'slug': 'claimresponse', 'call_type': 'fhir', 'resources': ['ClaimResponse']},
    {'name': 'ClinicalImpression', 'slug': 'clinicalimpression', 'call_type': 'fhir', 'resources': ['ClinicalImpression']},
    {'name': 'CodeSystem', 'slug': 'codesystem', 'call_type': 'fhir', 'resources': ['CodeSystem']},
    {'name': 'Communication', 'slug': 'communication', 'call_type': 'fhir', 'resources': ['Communication']},
    {'name': 'CommunicationRequest', 'slug': 'communicationrequest', 'call_type': 'fhir', 'resources': ['CommunicationRequest']},
    {'name': 'CompartmentDefinition', 'slug': 'compartmentdefinition', 'call_type': 'fhir', 'resources': ['CompartmentDefinition']},
    {'name': 'Composition', 'slug': 'composition', 'call_type': 'fhir', 'resources': ['Composition']},
    {'name': 'ConceptMap', 'slug': 'conceptmap', 'call_type': 'fhir', 'resources': ['ConceptMap']},
    {'name': 'Condition', 'slug': 'condition', 'call_type': 'fhir', 'resources': ['Condition']},
    {'name': 'Consent', 'slug': 'consent', 'call_type': 'fhir', 'resources': ['Consent']},
    {'name': 'Contract', 'slug': 'contract', 'call_type': 'fhir', 'resources': ['Contract']},
    {'name': 'Coverage', 'slug': 'coverage', 'call_type': 'fhir', 'resources': ['Coverage']},
    {'name': 'DataElement', 'slug': 'dataelement', 'call_type': 'fhir', 'resources': ['DataElement']},
    {'name': 'DetectedIssue', 'slug': 'detectedissue', 'call_type': 'fhir', 'resources': ['DetectedIssue']},
    {'name': 'Device', 'slug': 'device', 'call_type': 'fhir', 'resources': ['Device']},
    {'name': 'DeviceComponent', 'slug': 'devicecomponent', 'call_type': 'fhir', 'resources': ['DeviceComponent']},
    {'name': 'DeviceMetric', 'slug': 'devicemetric', 'call_type': 'fhir', 'resources': ['DeviceMetric']},
    {'name': 'DeviceRequest', 'slug': 'devicerequest', 'call_type': 'fhir', 'resources': ['DeviceRequest']},
    {'name': 'DeviceUseStatement', 'slug': 'deviceusestatement', 'call_type': 'fhir', 'resources': ['DeviceUseStatement']},
    {'name': 'DiagnosticReport', 'slug': 'diagnosticreport', 'call_type': 'fhir', 'resources': ['DiagnosticReport']},
    {'name': 'DocumentManifest', 'slug': 'documentmanifest', 'call_type': 'fhir', 'resources': ['DocumentManifest']},
    {'name': 'DocumentReference', 'slug': 'documentreference', 'call_type': 'fhir', 'resources': ['DocumentReference']},
    {'name': 'EligibilityRequest', 'slug': 'eligibilityrequest', 'call_type': 'fhir', 'resources': ['EligibilityRequest']},
    {'name': 'EligibilityResponse', 'slug': 'eligibilityresponse', 'call_type': 'fhir', 'resources': ['EligibilityResponse']},
    {'name': 'Encounter', 'slug': 'encounter', 'call_type': 'fhir', 'resources': ['Encounter']},
    {'name': 'Endpoint', 'slug': 'endpoint', 'call_type': 'fhir', 'resources': ['Endpoint']},
    {'name': 'EnrollmentRequest', 'slug': 'enrollmentrequest', 'call_type': 'fhir', 'resources': ['EnrollmentRequest']},
    {'name': 'EnrollmentResponse', 'slug': 'enrollmentresponse', 'call_type': 'fhir', 'resources': ['EnrollmentResponse']},
    {'name': 'EpisodeOfCare', 'slug': 'episodeofcare', 'call_type': 'fhir', 'resources': ['EpisodeOfCare']},
    {'name': 'ExpansionProfile', 'slug': 'expansionprofile', 'call_type': 'fhir', 'resources': ['ExpansionProfile']},
    {'name': 'ExplanationOfBenefit', 'slug': 'explanationofbenefit', 'call_type': 'fhir', 'resources': ['ExplanationOfBenefit']},
    {'name': 'FamilyMemberHistory', 'slug': 'familymemberhistory', 'call_type': 'fhir', 'resources': ['FamilyMemberHistory']},
    {'name': 'Flag', 'slug': 'flag', 'call_type': 'fhir', 'resources': ['Flag']},
    {'name': 'Goal', 'slug': 'goal', 'call_type': 'fhir', 'resources': ['Goal']},
    {'name': 'GraphDefinition', 'slug': 'graphdefinition', 'call_type': 'fhir', 'resources': ['GraphDefinition']},
    {'name': 'Group', 'slug': 'group', 'call_type': 'fhir', 'resources': ['Group']},
    {'name': 'GuidanceResponse', 'slug': 'guidanceresponse', 'call_type': 'fhir', 'resources': ['GuidanceResponse']},
    {'name': 'HealthcareService', 'slug': 'healthcareservice', 'call_type': 'fhir', 'resources': ['HealthcareService']},
    {'name': 'ImagingManifest', 'slug': 'imagingmanifest', 'call_type': 'fhir', 'resources': ['ImagingManifest']},
    {'name': 'ImagingStudy', 'slug': 'imagingstudy', 'call_type': 'fhir', 'resources': ['ImagingStudy']},
    {'name': 'Immunization', 'slug': 'immunization', 'call_type': 'fhir', 'resources': ['Immunization']},
    {'name': 'ImmunizationRecommendation', 'slug': 'immunizationrecommendation', 'call_type': 'fhir', 'resources': ['ImmunizationRecommendation']},
    {'name': 'ImplementationGuide', 'slug': 'implementationguide', 'call_type': 'fhir', 'resources': ['ImplementationGuide']},
    {'name': 'Library', 'slug': 'library', 'call_type': 'fhir', 'resources': ['Library']},
    {'name': 'Linkage', 'slug': 'linkage', 'call_type': 'fhir', 'resources': ['Linkage']},
    {'name': 'List', 'slug': 'list', 'call_type': 'fhir', 'resources': ['List']},
    {'name': 'Location', 'slug': 'location', 'call_type': 'fhir', 'resources': ['Location']},
    {'name': 'Measure', 'slug': 'measure', 'call_type': 'fhir', 'resources': ['Measure']},
    {'name': 'MeasureReport', 'slug': 'measurereport', 'call_type': 'fhir', 'resources': ['MeasureReport']},
    {'name': 'Media', 'slug': 'media', 'call_type': 'fhir', 'resources': ['Media']},
    {'name': 'Medication', 'slug': 'medication', 'call_type': 'fhir', 'resources': ['Medication']},
    {'name': 'MedicationAdministration', 'slug': 'medicationadministration', 'call_type': 'fhir', 'resources': ['MedicationAdministration']},
    {'name': 'MedicationDispense', 'slug': 'medicationdispense', 'call_type': 'fhir', 'resources': ['MedicationDispense']},
    {'name': 'MedicationRequest', 'slug': 'medicationrequest', 'call_type': 'fhir', 'resources': ['MedicationRequest']},
    {'name': 'MedicationStatement', 'slug': 'medicationstatement', 'call_type': 'fhir', 'resources': ['MedicationStatement']},
    {'name': 'MessageDefinition', 'slug': 'messagedefinition', 'call_type': 'fhir', 'resources': ['MessageDefinition']},
    {'name': 'MessageHeader', 'slug': 'messageheader', 'call_type': 'fhir', 'resources': ['MessageHeader']},
    {'name': 'NamingSystem', 'slug': 'namingsystem', 'call_type': 'fhir', 'resources': ['NamingSystem']},
    {'name': 'NutritionOrder', 'slug': 'nutritionorder', 'call_type': 'fhir', 'resources': ['NutritionOrder']},
    # Observation mixes labs and vital-signs
    {'name': 'Observation', 'slug': 'observation', 'call_type': 'skip', 'resources': ['Observation']},
    # Split to vital-signs
    {'name': 'VitalSigns', 'slug': 'vitalsigns', 'call_type': 'custom', 'resources': ['Observation']},
    # Split to Lab Results
    {'name': 'LabResults', 'slug': 'labresults', 'call_type': 'custom', 'resources': ['Observation']},
    #
    {'name': 'OperationDefinition', 'slug': 'operationdefinition', 'call_type': 'fhir', 'resources': ['OperationDefinition']},
    {'name': 'OperationOutcome', 'slug': 'operationoutcome', 'call_type': 'fhir', 'resources': ['OperationOutcome']},
    {'name': 'Organization', 'slug': 'organization', 'call_type': 'fhir', 'resources': ['Organization']},
    {'name': 'Parameters', 'slug': 'parameters', 'call_type': 'fhir', 'resources': ['Parameters']},
    {'name': 'Patient', 'slug': 'patient', 'call_type': 'fhir', 'resources': ['Patient']},
    {'name': 'PaymentNotice', 'slug': 'paymentnotice', 'call_type': 'fhir', 'resources': ['PaymentNotice']},
    {'name': 'PaymentReconciliation', 'slug': 'paymentreconciliation', 'call_type': 'fhir', 'resources': ['PaymentReconciliation']},
    {'name': 'Person', 'slug': 'person', 'call_type': 'fhir', 'resources': ['Person']},
    {'name': 'PlanDefinition', 'slug': 'plandefinition', 'call_type': 'fhir', 'resources': ['PlanDefinition']},
    {'name': 'Practitioner', 'slug': 'practitioner', 'call_type': 'fhir', 'resources': ['Practitioner']},
    {'name': 'PractitionerRole', 'slug': 'practitionerrole', 'call_type': 'fhir', 'resources': ['PractitionerRole']},
    {'name': 'Procedure', 'slug': 'procedure', 'call_type': 'fhir', 'resources': ['Procedure']},
    {'name': 'ProcedureRequest', 'slug': 'procedurerequest', 'call_type': 'fhir', 'resources': ['ProcedureRequest']},
    {'name': 'ProcessRequest', 'slug': 'processrequest', 'call_type': 'fhir', 'resources': ['ProcessRequest']},
    {'name': 'ProcessResponse', 'slug': 'processresponse', 'call_type': 'fhir', 'resources': ['ProcessResponse']},
    {'name': 'Provenance', 'slug': 'provenance', 'call_type': 'fhir', 'resources': ['Provenance']},
    {'name': 'Questionnaire', 'slug': 'questionnaire', 'call_type': 'fhir', 'resources': ['Questionnaire']},
    {'name': 'QuestionnaireResponse', 'slug': 'questionnaireresponse', 'call_type': 'fhir', 'resources': ['QuestionnaireResponse']},
    {'name': 'ReferralRequest', 'slug': 'referralrequest', 'call_type': 'fhir', 'resources': ['ReferralRequest']},
    {'name': 'RelatedPerson', 'slug': 'relatedperson', 'call_type': 'fhir', 'resources': ['RelatedPerson']},
    {'name': 'RequestGroup', 'slug': 'requestgroup', 'call_type': 'fhir', 'resources': ['RequestGroup']},
    {'name': 'ResearchStudy', 'slug': 'researchstudy', 'call_type': 'fhir', 'resources': ['ResearchStudy']},
    {'name': 'ResearchSubject', 'slug': 'researchsubject', 'call_type': 'fhir', 'resources': ['ResearchSubject']},
    {'name': 'RiskAssessment', 'slug': 'riskassessment', 'call_type': 'fhir', 'resources': ['RiskAssessment']},
    {'name': 'Schedule', 'slug': 'schedule', 'call_type': 'fhir', 'resources': ['Schedule']},
    {'name': 'SearchParameter', 'slug': 'searchparameter', 'call_type': 'fhir', 'resources': ['SearchParameter']},
    {'name': 'Sequence', 'slug': 'sequence', 'call_type': 'fhir', 'resources': ['Sequence']},
    {'name': 'ServiceDefinition', 'slug': 'servicedefinition', 'call_type': 'fhir', 'resources': ['ServiceDefinition']},
    {'name': 'Slot', 'slug': 'slot', 'call_type': 'fhir', 'resources': ['Slot']},
    {'name': 'Specimen', 'slug': 'specimen', 'call_type': 'fhir', 'resources': ['Specimen']},
    {'name': 'StructureDefinition', 'slug': 'structuredefinition', 'call_type': 'fhir', 'resources': ['StructureDefinition']},
    {'name': 'StructureMap', 'slug': 'structuremap', 'call_type': 'fhir', 'resources': ['StructureMap']},
    {'name': 'Subscription', 'slug': 'subscription', 'call_type': 'fhir', 'resources': ['Subscription']},
    {'name': 'Substance', 'slug': 'substance', 'call_type': 'fhir', 'resources': ['Substance']},
    {'name': 'SupplyDelivery', 'slug': 'supplydelivery', 'call_type': 'fhir', 'resources': ['SupplyDelivery']},
    {'name': 'SupplyRequest', 'slug': 'supplyrequest', 'call_type': 'fhir', 'resources': ['SupplyRequest']},
    {'name': 'Task', 'slug': 'task', 'call_type': 'fhir', 'resources': ['Task']},
    {'name': 'TestScript', 'slug': 'testscript', 'call_type': 'fhir', 'resources': ['TestScript']},
    {'name': 'TestReport', 'slug': 'testreport', 'call_type': 'fhir', 'resources': ['TestReport']},
    {'name': 'ValueSet', 'slug': 'valueset', 'call_type': 'fhir', 'resources': ['ValueSet']},
    {'name': 'VisionPrescription', 'slug': 'visionprescription', 'call_type': 'fhir', 'resources': ['VisionPrescription']}
]
