from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from ..util import parse_timestamp
from .model import DataModel
from .types import (
    Address,
    Attachment,
    CodeableConcept,
    ContactPoint,
    HumanName,
    Identifier,
    Period,
    Reference,
)


@dataclass
class PractitionerQualification(DataModel):
    identifier: List[Identifier] = field(default_factory=list)
    code: CodeableConcept = None
    period: Period = None
    issuer: Reference = None

    CONVERTERS = dict(
        identifier=[lambda value: [Identifier.from_data(val) for val in value]],
        code=[CodeableConcept.from_data],
        period=[Period.from_data],
        issuer=[Reference.from_data],
    )


@dataclass
class Practitioner(DataModel):
    """http://hl7.org/fhir/STU3/practitioner.html"""

    id: str

    identifier: List[Identifier] = field(default_factory=list)
    active: bool = None
    name: List[HumanName] = field(default_factory=list)
    telecom: List[ContactPoint] = field(default_factory=list)
    address: List[Address] = field(default_factory=list)
    gender: str = None  # male | female | other | unknown
    birthDate: datetime = None
    photo: List[Attachment] = field(default_factory=list)
    qualification: List[PractitionerQualification] = field(default_factory=list)
    communication: List[CodeableConcept] = field(default_factory=list)

    CONVERTERS = dict(
        identifier=[lambda value: [Identifier.from_data(val) for val in value]],
        name=[lambda value: [HumanName.from_data(val) for val in value]],
        telecom=[lambda value: [ContactPoint.from_data(val) for val in value]],
        address=[lambda value: [Address.from_data(val) for val in value]],
        birthDate=[parse_timestamp],
        photo=[lambda value: [Attachment.from_data(val) for val in value]],
        qualification=[
            lambda value: [PractitionerQualification.from_data(val) for val in value]
        ],
        communication=[lambda value: [CodeableConcept.from_data(val) for val in value]],
    )

    @property
    def names_text(self):
        return '; '.join(name.text for name in self.name)

    def next_encounter(self, encounters):
        return next(
            iter(
                encounter
                for encounter in encounters
                if self.id
                in [
                    participant.individual.reference.split('/')[-1]
                    for participant in encounter.participant
                ]
            ),
            None,
        )
