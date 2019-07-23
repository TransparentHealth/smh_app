from datetime import datetime
from dataclasses import dataclass, field
from typing import List
from .model import DataModel
from ..util import parse_timestamp


@dataclass
class Coding(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#Coding"""

    system: str = field(default=None)
    version: str = field(default=None)
    code: str = field(default=None)
    display: str = field(default=None)
    userSelected: bool = field(default=None)


@dataclass
class CodeableConcept(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#CodeableConcept"""

    coding: List[Coding] = field(default_factory=list)
    text: str = field(default=None)

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

    start: datetime = field(default=None)
    end: datetime = field(default=None)

    CONVERTERS = dict(start=[parse_timestamp], end=[parse_timestamp])


@dataclass
class Reference(DataModel):
    """http://hl7.org/fhir/STU3/references.html#Reference"""

    reference: str = field(default=None)
    identifier: dict = field(default=None)
    display: str = field(default=None)

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

    use: str = field(default=None)
    type: CodeableConcept = field(default_factory=CodeableConcept)
    system: str = field(default=None)
    value: str = field(default=None)
    period: Period = field(default_factory=Period)
    assigner: Reference = field(default_factory=Reference)


@dataclass
class Annotation(DataModel):
    text: str = field()
    authorReference: Reference = field(default_factory=Reference)
    authorString: str = field(default=None)
    time: datetime = field(default=None)

    CONVERTERS = dict(time=[parse_timestamp])
