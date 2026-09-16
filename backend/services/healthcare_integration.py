from backend.domain.patient import Patient
from backend.integrations.abdm import AbdmClient
from backend.integrations.fhir import FhirClient, FhirEncounter, FhirPatient
from backend.integrations.his import HisClient, HisEncounter, HisPatient


class HealthcareIntegrationService:
    def __init__(self, abdm_client: AbdmClient, fhir_client: FhirClient, his_client: HisClient) -> None:
        self.abdm_client = abdm_client
        self.fhir_client = fhir_client
        self.his_client = his_client

    async def sync_patient(self, patient: Patient) -> Patient:
        abha_profile = None

        if patient.abha_reference is not None:
            abha_profile = await self.abdm_client.get_profile(patient.abha_reference)

        display_name = patient.display_name
        date_of_birth = patient.date_of_birth

        if abha_profile is not None:
            display_name = abha_profile.display_name
            if abha_profile.date_of_birth is not None:
                from datetime import date
                date_of_birth = date.fromisoformat(abha_profile.date_of_birth)

        fhir_patient = FhirPatient(
            patient_id=patient.patient_id,
            abha_id=patient.abha_reference,
            display_name=display_name,
            date_of_birth=date_of_birth.isoformat() if date_of_birth is not None else None,
        )

        his_patient = HisPatient(
            patient_id=patient.patient_id,
            hospital_reference=patient.hospital_reference or patient.patient_id,
            display_name=display_name,
            date_of_birth=date_of_birth.isoformat() if date_of_birth is not None else None,
        )

        await self.fhir_client.upsert_patient(fhir_patient)
        await self.his_client.upsert_patient(his_patient)

        return patient

    async def create_encounter(self, session_id: str, patient_id: str, department_id: str) -> str:
        encounter_id = f"encounter_{session_id}"

        fhir_encounter = FhirEncounter(
            encounter_id=encounter_id,
            patient_id=patient_id,
            department_id=department_id,
            status="planned",
        )

        his_encounter = HisEncounter(
            encounter_id=encounter_id,
            patient_id=patient_id,
            department_id=department_id,
            status="scheduled",
        )

        await self.fhir_client.create_encounter(fhir_encounter)
        await self.his_client.create_encounter(his_encounter)

        return encounter_id

    async def update_encounter_status(self, encounter_id: str, status: str) -> None:
        await self.fhir_client.update_encounter_status(encounter_id, status)
        await self.his_client.update_encounter_status(encounter_id, status)
