from dataclasses import dataclass
from typing import Protocol


@dataclass
class FhirPatient:
    patient_id: str
    abha_id: str | None
    display_name: str
    date_of_birth: str | None = None


@dataclass
class FhirEncounter:
    encounter_id: str
    patient_id: str
    department_id: str
    status: str


@dataclass
class FhirDocumentReference:
    document_reference_id: str
    patient_id: str
    document_id: str
    document_type: str
    title: str


class FhirClient(Protocol):
    async def upsert_patient(self, patient: FhirPatient) -> FhirPatient:
        ...

    async def create_encounter(self, encounter: FhirEncounter) -> FhirEncounter:
        ...

    async def update_encounter_status(self, encounter_id: str, status: str) -> FhirEncounter | None:
        ...

    async def create_document_reference(self, document: FhirDocumentReference) -> FhirDocumentReference:
        ...


class MockFhirClient:
    def __init__(self) -> None:
        self.patients: dict[str, FhirPatient] = {}
        self.encounters: dict[str, FhirEncounter] = {}
        self.documents: dict[str, FhirDocumentReference] = {}

    async def upsert_patient(self, patient: FhirPatient) -> FhirPatient:
        self.patients[patient.patient_id] = patient
        return patient

    async def create_encounter(self, encounter: FhirEncounter) -> FhirEncounter:
        self.encounters[encounter.encounter_id] = encounter
        return encounter

    async def update_encounter_status(self, encounter_id: str, status: str) -> FhirEncounter | None:
        encounter = self.encounters.get(encounter_id)

        if encounter is None:
            return None

        encounter.status = status
        return encounter

    async def create_document_reference(self, document: FhirDocumentReference) -> FhirDocumentReference:
        self.documents[document.document_reference_id] = document
        return document
