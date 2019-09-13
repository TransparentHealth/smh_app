from dataclasses import dataclass, field
from typing import List
from .medication import Medication, MedicationRequest, MedicationStatement
from .model import DataModel


@dataclass
class Prescription(DataModel):
    """Prescription is a combination of Medication, """

    id: str = field(default=None)
    medication: Medication = field(default_factory=Medication)
    requests: List[MedicationRequest] = field(default_factory=list)
    statements: List[MedicationStatement] = field(default_factory=list)

    def __post_init__(self):
        if self.medication:
            self.id = self.medication.id
