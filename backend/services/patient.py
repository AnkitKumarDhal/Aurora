from datetime import datetime, timezone

from backend.database.repositories.patient import PatientRepository
from backend.domain.patient import Patient
from backend.models.patient import PatientDocument


class PatientService:
    def __init__(self, repository: PatientRepository) -> None:
        self.repository = repository

    async def get_patient(self, patient_id: str) -> Patient | None:
        document = await self.repository.get_patient(patient_id)

        if document is None:
            return None

        return self._to_domain(document)

    async def get_by_abha_reference(
        self,
        abha_reference: str,
    ) -> Patient | None:
        document = await self.repository.get_by_abha_reference(
            abha_reference,
        )

        if document is None:
            return None

        return self._to_domain(document)

    async def get_by_hospital_reference(
        self,
        hospital_reference: str,
    ) -> Patient | None:
        document = await self.repository.get_by_hospital_reference(
            hospital_reference,
        )

        if document is None:
            return None

        return self._to_domain(document)

    async def create_patient(self, patient: Patient) -> Patient:
        document = self._to_document(patient)
        await self.repository.create_patient(document)
        return patient

    async def update_patient(
        self,
        patient_id: str,
        updates: dict,
    ) -> Patient | None:
        document = await self.repository.update_patient(
            patient_id,
            updates,
        )

        if document is None:
            return None

        return self._to_domain(document)

    @staticmethod
    def _to_domain(document: PatientDocument) -> Patient:
        return Patient(
            patient_id=document.patient_id,
            display_name=document.display_name,
            date_of_birth=document.date_of_birth,
            age=document.age,
            abha_reference=document.abha_reference,
            hospital_reference=document.hospital_reference,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _to_document(patient: Patient) -> PatientDocument:
        return PatientDocument(
            patient_id=patient.patient_id,
            display_name=patient.display_name,
            date_of_birth=patient.date_of_birth,
            age=patient.age,
            abha_reference=patient.abha_reference,
            hospital_reference=patient.hospital_reference,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )
