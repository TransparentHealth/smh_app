from dataclasses import dataclass, field
from typing import List

from .model import DataModel
from .types import CodeableConcept, Identifier, Period, Reference


@dataclass
class EncounterParticipant(DataModel):
    type: List[CodeableConcept] = field(default_factory=list)
    period: Period = field(default_factory=Period)
    individual: Reference = field(default_factory=Reference)

    print("Period:", Period)

    CONVERTERS = {
        'type': [lambda value: [CodeableConcept.from_data(val) for val in value]],
    }

    # CONVERTERS = {
    #     'type': [lambda value: [CodeableConcept.from_data(val) for val in value]],
    #     'period': [Period.from_data],
    #     'individual': [Reference.from_data],
    # }


@dataclass
class EncounterLocation(DataModel):
    location: Reference = field(default_factory=Reference)

    # CONVERTERS = {'location': [Reference.from_data]}

@dataclass
class Encounter(DataModel):

    id: str = field()
    status: str = field()

    identifier: List[Identifier] = field(default_factory=list)
    type: List[CodeableConcept] = field(default_factory=list)
    subject: Reference = field(default_factory=Reference)
    participant: List[EncounterParticipant] = field(default_factory=list)
    period: Period = field(default=None)
    location: List[EncounterLocation] = field(default_factory=list)

    CONVERTERS = {
        'identifier': [lambda value: [Identifier.from_data(val) for val in value]],
        'type': [lambda value: [CodeableConcept.from_data(val) for val in value]],
        'subject': [Reference.from_data],
        'participant': [
            lambda value: [EncounterParticipant.from_data(val) for val in value]
        ],
        'period': [Period.from_data],
        'location': [lambda value: [EncounterLocation.from_data(val) for val in value]],
    }
    VALIDATORS = {
        'status': [
            lambda instance, field, value: value.text
            in ['planned', 'arrived', 'triaged', 'in-progress', 'onleave']
            + ['finished', 'cancelled', 'entered-in-error', 'unknown']
        ]
    }

    @property
    def locations_display(self):
        return '; '.join(l.location.display for l in self.location)
