from dataclasses import dataclass, field
from typing import List

from .model import DataModel
from .types import CodeableConcept, Identifier, Period, Quantity, Reference


@dataclass
class Medication(DataModel):
    """http://hl7.org/fhir/STU3/medication.html"""

    id: str = field()  # required
    code: CodeableConcept = None

    CONVERTERS = dict(code=[CodeableConcept.from_data])


@dataclass
class MedicationRequester(DataModel):
    agent: Reference = None
    onBehalfOf: Reference = None

    CONVERTERS = dict(agent=[Reference.from_data], onBehalfOf=[Reference.from_data])

    VALIDATORS = dict(
        agent=[
            lambda instance, field, value: not value
            or not value.resourceType
            or value.resourceType
            in ['Practitioner', 'Organization', 'Patient', 'RelatedPerson', 'Device']
        ],
        onBehalfOf=[
            lambda instance, field, value: not value
            or not value.resourceType
            or value.resourceType in ['Organization']
        ],
    )


@dataclass
class MedicationRequest(DataModel):
    """http://hl7.org/fhir/STU3/medicationrequest.html"""

    # required
    id: str = field()
    subject: Reference = field()

    identifier: Identifier = None
    medicationReference: Reference = None
    requester: MedicationRequester = None
    subject: Reference = None

    CONVERTERS = dict(
        identifier=[Identifier.from_data],
        medicationReference=[Reference.from_data],
        requester=[MedicationRequester.from_data],
        subject=[Reference.from_data],
    )


@dataclass
class Dosage(DataModel):
    """http://hl7.org/fhir/STU3/dosage.html#Dosage"""

    doseQuantity: Quantity = None

    CONVERTERS = dict(doseQuantity=[Quantity.from_data])


@dataclass
class MedicationStatement(DataModel):
    """http://hl7.org/fhir/STU3/medicationstatement.html"""

    # required
    id: str = field()
    status: str = field()
    taken: str = field()

    identifier: List[Identifier] = field(default_factory=list)
    subject: Reference = None
    medicationReference: Reference = None
    effectivePeriod: Period = None
    dosage: List[Dosage] = field(default_factory=list)

    def __str__(self):
        """Provide a string representation that focuses on the key distinguishing data"""
        return (
            f"MedicationStatement(medication='{self.medicationReference.display}'"
            + f", subject='{self.subject.display}'"
            + f", effectivePeriod=('{self.effectivePeriod.start}', '{self.effectivePeriod.end}'"
            + f", dosage=["
            + ', '.join(
                [
                    f"'{dose.doseQuantity.value} {dose.doseQuantity.unit}'"
                    for dose in self.dosage
                ]
            )
            + '])'
        )

    CONVERTERS = dict(
        identifier=[lambda value: [Identifier.from_data(val) for val in value]],
        subject=[Reference.from_data],
        medicationReference=[Reference.from_data],
        effectivePeriod=[Period.from_data],
        dosage=[lambda value: [Dosage.from_data(val) for val in value]],
    )

    VALIDATORS = dict(
        status=[
            lambda instance, field, value: value
            in [
                'active',
                'completed',
                'entered-in-error',
                'intended',
                'stopped',
                'on-hold',
            ]
        ],
        taken=[lambda instance, field, value: value in ['y', 'n', 'unk', 'na']],
    )
