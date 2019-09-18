from dataclasses import dataclass, field
from typing import List

from .model import DataModel
from .types import CodeableConcept, Reference


@dataclass
class Condition(DataModel):
    """http://hl7.org/fhir/STU3/condition.html"""

    id: str

    clinicalStatus: str = field(default=None)
    verificationStatus: str = field(default=None)
    category: List[CodeableConcept] = field(default_factory=list)
    code: CodeableConcept = field(default_factory=CodeableConcept)
    subject: Reference = field(default_factory=Reference)

    CONVERTERS = {
        'category': [lambda value: [CodeableConcept.from_data(val) for val in value]],
        'code': [CodeableConcept.from_data],
        'subject': [Reference.from_data],
    }
    VALIDATORS = {
        'clinicalStatus': [
            lambda instance, attribute, value: (
                value in ['active', 'recurrence', 'inactive', 'remission', 'resolved']
            )
        ],
        'verificationStatus': [
            lambda instance, attribute, value: (
                value
                in ['provisional', 'differential', 'confirmed']
                + ['refuted', 'entered-in-error', 'unknown']
            )
        ],
    }
