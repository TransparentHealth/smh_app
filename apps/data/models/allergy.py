from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from ..util import parse_timestamp
from .model import DataModel
from .types import Annotation, CodeableConcept, Reference


@dataclass
class AllergyReaction(DataModel):
    # required
    manifestation: List[CodeableConcept] = field()

    # not required
    substance: CodeableConcept = field(default_factory=CodeableConcept)
    description: str = field(default=None)
    onset: datetime = field(default=None)
    severity: str = field(default=None)
    exposureRoute: CodeableConcept = field(default_factory=CodeableConcept)
    note: str = field(default=None)

    CONVERTERS = dict(
        manifestation=[lambda value: [CodeableConcept.from_data(val) for val in value]],
        substance=[CodeableConcept.from_data],
        onset=[parse_timestamp],
        exposureRoute=[CodeableConcept.from_data],
    )

    VALIDATORS = dict(
        severity=[
            lambda instance, field, value: not value
            or value in ['mild', 'moderate', 'severe']
        ]
    )


@dataclass
class AllergyIntolerance(DataModel):
    """http://hl7.org/fhir/STU3/allergyintolerance.html"""

    # required
    id: int = field()

    # not required
    patient: Reference = field(default_factory=Reference)
    clinicalStatus: CodeableConcept = field(default_factory=CodeableConcept)
    verificationStatus: CodeableConcept = field(default_factory=CodeableConcept)
    type: str = field(default=None)
    category: List[str] = field(default_factory=list)
    criticality: str = field(default=None)
    code: CodeableConcept = field(default_factory=CodeableConcept)
    encounter: int = field(default=None)
    onsetDateTime: datetime = field(default=None)
    recorder: Reference = field(default_factory=Reference)
    recordedDate: datetime = field(default=None)  # per FHIR spec
    asserter: Reference = field(default_factory=Reference)
    assertedDate: datetime = field(default=None)  # as in our data
    lastOccurrence: datetime = field(default=None)
    note: List[Annotation] = field(default_factory=list)
    reaction: List[AllergyReaction] = field(default_factory=list)

    CONVERTERS = dict(
        patient=[Reference.from_data],
        clinicalStatus=[CodeableConcept.from_data],
        verificationStatus=[CodeableConcept.from_data],
        category=[list],
        code=[CodeableConcept.from_data],
        onsetDateTime=[parse_timestamp],
        recorder=[Reference.from_data],
        recordedDate=[parse_timestamp],
        asserter=[Reference.from_data],
        assertedDate=[parse_timestamp],
        lastOccurrence=[parse_timestamp],
        note=[lambda value: [Annotation.from_data(val) for val in value]],
        reaction=[lambda value: [AllergyReaction.from_data(val) for val in value]],
    )

    VALIDATORS = dict(
        clinicalStatus=[
            lambda instance, field, value: not value
            or value.text in ['active', 'inactive', 'resolved']
        ],
        verificationStatus=[
            lambda instance, field, value: not value
            or value.text in ['unconfirmed', 'confirmed', 'refuted', 'entered-in-error']
        ],
        type=[
            lambda instance, field, value: not value
            or value in ['allergy', 'intolerance']
        ],
        category=[
            lambda instance, field, value: not value
            or all(
                [
                    val in ['food', 'medication', 'environment', 'biologic']
                    for val in value
                ]
            )
        ],
        criticality=[
            lambda instance, field, value: not value
            or value in ['low', 'high', 'unable-to-assess']
        ],
        recorder=[
            lambda instance, field, value: not value
            or not value.resourceType
            or value.resourceType
            in ['Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson']
        ],
        asserter=[
            lambda instance, field, value: not value
            or not value.resourceType
            or value.resourceType
            in ['Patient', 'RelatedPerson', 'Practitioner', 'PractitionerRole']
        ],
    )
