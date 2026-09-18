from .base import BaseRepository
from backend.models.patient import PatientDocument


class PatientRepository(BaseRepository[PatientDocument]):
    collection_name = PatientDocument.collection_name
    model = PatientDocument

    async def get_patient(self, patient_id: str) -> PatientDocument | None:
        return await self.get_one({"patient_id": patient_id})

    async def get_by_abha_reference(self, abha_reference: str) -> PatientDocument | None:
        return await self.get_one({"abha_reference": abha_reference})

    async def get_by_aadhaar_reference(self, aadhaar_reference: str) -> PatientDocument | None:
        return await self.get_one({"aadhaar_reference": aadhaar_reference})

    async def get_by_hospital_reference(self, hospital_reference: str) -> PatientDocument | None:
        return await self.get_one({"hospital_reference": hospital_reference})

    async def create_patient(self, patient: PatientDocument) -> PatientDocument:
        return await self.create(patient)

    async def update_patient(self, patient_id: str, updates: dict) -> PatientDocument | None:
        return await self.update_one({"patient_id": patient_id}, updates)
