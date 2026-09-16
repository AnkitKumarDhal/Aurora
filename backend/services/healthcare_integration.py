from backend.domain.patient import Patient
from backend.integrations.abdm import AbdmClient
from backend.integrations.fhir import FhirClient, FhirPatient
from backend.integrations.his import HisClient, HisPatient


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
