from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from ..util import parse_timestamp
from .model import DataModel


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

    def __str__(self):
        return self.text or '–'

    @classmethod
    def from_data(cls, value):
        """ CodeableConcept are sometimes given as plain strings;
        interpret as the "text" value
        """
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

    # The following is necessary because Identifier is defined below and
    # depends on Reference
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
    # period: Period = field(default_factory=Period)
    assigner: Reference = field(default_factory=Reference)

    CONVERTERS = dict(
        type=[CodeableConcept.from_data],
        assigner=[Reference.from_data],
    )

    # CONVERTERS = dict(
    #     type=[CodeableConcept.from_data],
    #     period=[Period.from_data],
    #     assigner=[Reference.from_data],
    # )


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

    def __str__(self):
        return f"{self.value or '–'}{self.unit or ''}".strip()


@dataclass
class HumanName(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#HumanName"""

    use: str = None  # usual | official | temp | nickname | anonymous | old | maiden
    text: str = None
    family: str = None
    given: List[str] = field(default_factory=list)
    prefix: list = field(default_factory=list)
    suffix: list = field(default_factory=list)
    period: Period = None

    CONVERTERS = dict(period=[Period.from_data], given=[list])

    def __post_init__(self):
        if not self.text:
            tokens = self.prefix + self.given + [self.family or ''] + self.suffix
            self.text = ' '.join([token for token in tokens if token])


@dataclass
class ContactPoint(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#ContactPoint"""

    system: str = None  # phone | fax | email | pager | url | sms | other
    value: str = None
    use: str = None  # home | work | temp | old | mobile
    rank: int = None
    period: Period = None

    CONVERTERS = dict(period=[Period.from_data])

    def __str__(self):
        return f"{self.system or ''}{':' if self.system else ''} {self.value}".strip()


@dataclass
class Address(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#Address"""

    use: str = None  # home | work | temp | old
    type: str = None  # postal | physical | both
    text: str = None
    line: List[str] = field(default_factory=list)
    city: str = None
    district: str = None
    state: str = None
    postalCode: str = None
    country: str = None
    period: Period = None

    CONVERTERS = dict(period=[Period.from_data], line=[list])

    @property
    def lines(self):
        return [
            line
            for line in self.line
            + [
                f"{self.city}{', ' if self.state else ''}{self.state or ''} {self.postalCode or ''}".strip(),
                f"{self.district or ''} {self.country or ''}".strip(),
            ]
            if line
        ]

    def __str__(self):
        return ', '.join(self.lines)

    def html(self):
        return '<br/>'.join(self.lines)


@dataclass
class Attachment(DataModel):
    """http://hl7.org/fhir/STU3/datatypes.html#Attachment"""

    contentType: str = None
    language: str = None
    data: str = None
    url: str = None
    size: int = None
    hash: str = None
    title: str = None
    creation: datetime = None

    CONVERTERS = dict(creation=[parse_timestamp])
