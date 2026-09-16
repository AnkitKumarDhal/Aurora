from dataclasses import dataclass
from typing import Protocol


@dataclass
class HisPatient:
    patient_id: str
    hospital_reference: str
    display_name: str
    date_of_birth: str | None = None


@dataclass
class HisEncounter:
    encounter_id: str
    patient_id: str
    department_id: str
    status: str


class HisClient(Protocol):
    async def upsert_patient(self, patient: HisPatient) -> HisPatient:
        ...

    async def create_encounter(self, encounter: HisEncounter) -> HisEncounter:
        ...

    async def update_encounter_status(self, encounter_id: str, status: str) -> HisEncounter | None:
        ...


class MockHisClient:
    def __init__(self) -> None:
        self.patients: dict[str, HisPatient] = {}
        self.encounters: dict[str, HisEncounter] = {}

    async def upsert_patient(self, patient: HisPatient) -> HisPatient:
        self.patients[patient.patient_id] = patient
        return patient

    async def create_encounter(self, encounter: HisEncounter) -> HisEncounter:
        self.encounters[encounter.encounter_id] = encounter
        return encounter

    async def update_encounter_status(self, encounter_id: str, status: str) -> HisEncounter | None:
        encounter = self.encounters.get(encounter_id)

        if encounter is None:
            return None

        encounter.status = status
        return encounter
