import pytest

from backend.domain.patient import Patient
from backend.integrations.abdm import MockAbdmClient
from backend.integrations.fhir import MockFhirClient
from backend.integrations.his import MockHisClient
from backend.services.healthcare_integration import HealthcareIntegrationService


@pytest.mark.asyncio
async def test_sync_patient():
    abdm_client = MockAbdmClient()
    fhir_client = MockFhirClient()
    his_client = MockHisClient()

    service = HealthcareIntegrationService(
        abdm_client=abdm_client,
        fhir_client=fhir_client,
        his_client=his_client,
    )

    patient = Patient(
        patient_id="patient-demo-001",
        display_name="Local Name",
        abha_reference="11-22-33-44-55-66",
        hospital_reference="HOSP-0001",
    )

    result = await service.sync_patient(patient)

    assert result is patient
    assert fhir_client.patients["patient-demo-001"].display_name == "Demo Patient"
    assert fhir_client.patients["patient-demo-001"].abha_id == "11-22-33-44-55-66"
    assert his_client.patients["patient-demo-001"].display_name == "Demo Patient"
    assert his_client.patients["patient-demo-001"].hospital_reference == "HOSP-0001"
