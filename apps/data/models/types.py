from datetime import datetime
from dataclasses import dataclass, field
from typing import List
from .model import DataModel
from ..util import parse_timestamp


@dataclass
class Coding(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#Coding"""

    system: str = None
    version: str = None
    code: str = None
    display: str = None
    userSelected: bool = None


@dataclass
class CodeableConcept(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#CodeableConcept"""

    coding: List[Coding] = field(default_factory=list)
    text: str = None

    CONVERTERS = dict(coding=[lambda value: [Coding.from_data(val) for val in value]])

    @classmethod
    def from_data(cls, value):
        """CodeableConcept are sometimes given as plain strings; interpret as the "text" value"""
        if isinstance(value, str):
            return cls(text=value)
        else:
            return super().from_data(value)


@dataclass
class Period(DataModel):
    """http://www.hl7.org/fhir/STU3/datatypes.html#Period"""

    start: datetime = None
    end: datetime = None

    CONVERTERS = dict(start=[parse_timestamp], end=[parse_timestamp])


@dataclass
class Reference(DataModel):
    """http://hl7.org/fhir/STU3/references.html#Reference"""

    reference: str = None
    identifier: dict = None
    display: str = None

    # The following is necessary because Identifier is defined below and depends on Reference
    def __post_init__(self):
        super().__post_init__()
        if self.identifier:
            self.identifier = Identifier.from_data(self.identifier)

    @property
    def resourceType(self):
        if self.reference and '/' in self.reference:
            return self.reference.split('/')[0]

    @property
    def id(self):
        if self.reference and '/' in self.reference:
            return self.reference.split('/')[1]


@dataclass
class Identifier(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#Identifier"""

    use: str = None
    type: CodeableConcept = field(default_factory=CodeableConcept)
    system: str = None
    value: str = None
    period: Period = field(default_factory=Period)
    assigner: Reference = field(default_factory=Reference)

    CONVERTERS = dict(
        type=[CodeableConcept.from_data], period=[Period.from_data], assigner=[Reference.from_data]
    )


@dataclass
class Annotation(DataModel):
    text: str = field()
    authorReference: Reference = field(default_factory=Reference)
    authorString: str = None
    time: datetime = None

    CONVERTERS = dict(time=[parse_timestamp])


@dataclass
class Quantity(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#Quantity"""

    value: float = None
    comparator: str = None
    unit: str = None
    system: str = None
    code: str = None

