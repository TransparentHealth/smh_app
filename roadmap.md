# FHIR Data Presentation Changes to SMH_APP and SHAREMYHEALTH
## Settings - ShareMyHealth
Discovered an issue with copying large files into HIE Profile. Added the following:

```
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440 * 4
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440 * 4
#  2621440 = 2.5Mb
```

Added lists for FHIR STU3 Resources and Vital-Signs

```
RESOURCES = [‘Account’, ‘ActivityDefinition’, ‘AllergyIntolerance’, ‘AdverseEvent’, ‘Appointment’,
             ‘AppointmentResponse’, ‘AuditEvent’, ‘Basic’, 'Binary', 'BodySite', 'Bundle',
             'CapabilityStatement', 'CarePlan', 'CareTeam', 'ChargeItem', 'Claim’, ‘ClaimResponse’,
             ‘ClinicalImpression’, ‘CodeSystem’, ‘Communication’, ‘CommunicationRequest’,
             'CompartmentDefinition', 'Composition', 'ConceptMap', 'Condition', 'Consent',
             'Contract', 'Coverage', 'DataElement', 'DetectedIssue', 'Device', 'DeviceComponent',
             'DeviceMetric', 'DeviceRequest', 'DeviceUseStatement', 'DiagnosticReport', 'DocumentManifest',
             'DocumentReference', 'EligibilityRequest', 'EligibilityResponse', 'Encounter', 'Endpoint',
             'EnrollmentRequest', 'EnrollmentResponse', 'EpisodeOfCare', 'ExpansionProfile',
             'ExplanationOfBenefit', 'FamilyMemberHistory', 'Flag', 'Goal', 'GraphDefinition',
             'Group', 'GuidanceResponse', 'HealthcareService', 'ImagingManifest', 'ImagingStudy',
             'Immunization', 'ImmunizationRecommendation', 'ImplementationGuide', 'Library', 'Linkage',
             ‘List’, ‘Location’, ‘Measure’, ‘MeasureReport’, ‘Media’,
             ‘Medication’, ‘MedicationAdministration’, ‘MedicationDispense’, ‘MedicationRequest',
             'MedicationStatement', 'MessageDefinition', 'MessageHeader', 'NamingSystem',
             ‘NutritionOrder’, ‘Observation’, ‘OperationDefinition’, ‘OperationOutcome’,
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


```
Added RESOURCES and VITALSIGNS to  SETTINGS_EXPORT

## Settings - SMH_APP

Discovered an issue with copying large files into HIE Profile. Added the following:

```
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440 * 4
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440 * 4
#  2621440 = 2.5Mb

JSON_INDENT = 4
```


## Constants.py - SMH_APP
apps/member/constants.py

Created RECORDS_STU3 = []

The structure of the dictionary entries in the list are as follows:

``` json

{‘name’: ‘AllergyIntolerance’, ‘slug’: ‘allergyintolerance’, ‘call_type’: ‘fhir’, ‘resources’: [‘AllergyIntolerance’],
 ‘display’: ‘Allergy Intolerance’,
 ‘headers’: [‘id’, ‘clinicalStatus', 'verificationStatus', 'category', '*'],
 'exclude': ['meta', 'identifier', 'resourceType', 'patient’],
 ‘field_formats’:[{“field”: “category”, “detail”: “$.category[*]”, “format”: “”},
                 {"field": "code", "detail": "$.code.text", "format": ""},
                 {"field": "onsetDateTime", "detail": "$.onsetDateTime[*]", "format": {"start": 0, "end": 10}},
                 {"field": "assertedDate", "detail": "$.assertedDate[*]", "format": {"start": 0, "end": 10}}
                 ]},

```

There is an entry for each FHIR STU3 resource from the base FHIR  STU3 Specification.

### Name
Official Resource Name
### Slug 
Lower case version of name, as used in urls
### call_type 
fhir | custom | skip

	- Set to “skip” to not process a resource
	- Set to “fhir” to process as a regular fhir resource
	- Set to “custom” to process via an alternate method

VitalSigns and LabResults are examples that use “custom” because the data for these types of information are mixed together in the Observation resource we use custom calls to separate the resources.

The separation is done using the VITALSIGNS constant in apps/member/fhir_requests.py. If the code in the Observation is one of those listed in VITALSIGNS then the resource is INCLUDED in VitalSigns and EXCLUDED from LabResults.

``` json
VITALSIGNS = [‘3141-9’, ‘8302-2’, ‘39156-5’,
              ‘8480-6’, ‘8462-4’, ‘8867-4’, ‘8310-5’, ‘9279-1’]

```

### Resources 
List of Resources to be included.  By default this would be a single entry list that is the Resource Name.

### Display 
Friendly Name to use for the title of the resource panel. Typically this is a version of name with spaces and Proper case.

### Headers 
List of fields to be included in the Heading on the display records page. ‘*’ can be added to allow all EXCEPT excluded fields to be displayed.

### Exclude
A list of fields to exclude from display. E.g. resourceType.

### field_formats
 
``` json
‘field_formats’:[{“field”: “category”, “detail”: “$.category[*]”, “format”: “”},
                 {"field": "code", "detail": "$.code.text", "format": ""},
                 {"field": "onsetDateTime", "detail": "$.onsetDateTime[*]", "format": {"start": 0, "end": 10}},
                 {"field": "assertedDate", "detail": "$.assertedDate[*]", "format": {"start": 0, "end": 10}}
                 ]

```

#### Field 
resource field name
#### Detail 
jsonPath expression to select content
#### Format 
formatting of selected values.

Date fields are presented as text using the ISO Time format.
A format dict of {"start": 0, "end": 10} will truncate the date to display YYYY-MM-DD.

Code also looks at the result from the json path statement and if Periods which have a Start and End data/time only the first value is displayed if both values are the same.

## ID field
The record displays use the ID field as a modal hyper link. Clinking this link will display the entire FHIR record using a pretty Print with indenting that is set using the JSON_INDENT value from settings.py.


## Future Enhancements
### Record Views
Each of the 20 resources that are currently converted by the cDA2FHIR Service need to have completed definitions in RECORDS_STU3.

AllergyIntolerance and DiagnosticReport have been built out so far. They can be used as a model for what needs to be displayed.

### Vital Signs custom view

Vital Signs have readings split across multiple Observation records. For example Blood Pressure is normally presented as:
	- Diastolic
	- Systolic
	- Pulse
These are three observations. We need to create a view that presents a custom vital signs view for a given date. This would present:
	- Weight
	- Height
	- Blood Pressure,

### Sorting
We need to implement sorting on the records.
We will typically want to do a reverse sort on a date field so that the latest information displays at the top.
This needs to be driven from a set of variables that can be supplied from RECORDS_STU3.

These variables may differ by resource, for example the name of the sort field, and the sort sequence.

Each Resource dict in RECORDS_STU3 could be updated to add:
``` json
‘Sort’: {‘field’: “”, ‘value’: “”, ‘reverse’: True | False}
```

### Friendly Field Names

Constants.py has the start of a list definition for Friendly Field Names:

``` json

FIELD_TITLES = [
    {‘profile’: ‘AllergyIntolerance’,
     ‘elements’: [
        {‘system_name’: ‘onsetDateTime’, “show_name”: ‘Onset’},
        {‘system_name’: ‘assertedDate’, “show_name”: ‘Asserted’},
    ]}
]

```

the friendlyfield templatetag now works.

```
{{ key|friendlyfield:resource_profile.name }}:<br/>{{ value }}
```
the tag is in apps/common/fhirtags.py


## Icons - SMH_APP
Each panel needs an icon.
The icon .png file should be 70x70 pixels
Each png filename should match the resource slug
Resource slug is in:
	- Contants.py
	- RECORDS_STU3[‘slug’]

