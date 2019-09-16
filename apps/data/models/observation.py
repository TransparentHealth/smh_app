from dataclasses import dataclass, field
from .model import DataModel
from .types import CodeableConcept, Period, Reference, Quantity


@dataclass
class Observation(DataModel):
    resourceType = 'Observation'

    id: str = field()
    status: str = field()
    code: CodeableConcept = field()

    subject: Reference = field(default_factory=Reference)
    effectivePeriod: Period = field(default_factory=Period)
    valueQuantity: Quantity = field(default_factory=Quantity)

    CONVERTERS = {
        'code': [CodeableConcept.from_data],
        'subject': [Reference.from_data],
        'effectivePeriod': [Period.from_data],
        'valueQuantity': [Quantity.from_data],
    }
    VALIDATORS = {
        'status': [
            lambda instance, field, value: value.text
            in ['registered', 'preliminary', 'final', 'amended']
        ],
        'subject': [
            lambda instance, field, value: not value
            or not value.resourceType
            or value.resourceType in ['Patient', 'Group', 'Device', 'Location']
        ],
    }
