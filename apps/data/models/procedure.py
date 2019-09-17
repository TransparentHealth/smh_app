from dataclasses import dataclass, field
from typing import List

from .model import DataModel
from .types import CodeableConcept, Period, Reference


@dataclass
class Performer(DataModel):
    actor: Reference
    role: CodeableConcept = field(default=None)
    onBehalfOf: Reference = field(default=None)

    CONVERTERS = {
        'actor': [Reference.from_data],
        'role': [CodeableConcept.from_data],
        'onBehalfOf': [lambda value: [Reference.from_data(val) for val in value]],
    }


@dataclass
class Procedure(DataModel):
    id: str
    subject: Reference
    status: str

    code: CodeableConcept = field(default_factory=CodeableConcept)
    context: Reference = field(default=None)
    performedPeriod: Period = field(default_factory=Period)
    performer: List[Performer] = field(default_factory=list)

    CONVERTERS = {
        'subject': [Reference.from_data],
        'code': [CodeableConcept.from_data],
        'performedPeriod': [Period.from_data],
        'performer': [lambda value: [Performer.from_data(val) for val in value]],
    }
    VALIDATORS = {
        'status': [
            lambda instance, attribute, value: (
                value
                in ['preparation', 'in-progress', 'suspended', 'aborted']
                + ['completed', 'entered-in-error', 'unknown']
            )
        ]
    }
