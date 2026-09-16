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


@pytest.mark.asyncio
async def test_create_encounter():
    fhir_client = MockFhirClient()
    his_client = MockHisClient()

    service = HealthcareIntegrationService(
        abdm_client=MockAbdmClient(),
        fhir_client=fhir_client,
        his_client=his_client,
    )

    encounter_id = await service.create_encounter(
        session_id="session-1",
        patient_id="patient-1",
        department_id="general-medicine",
    )

    assert encounter_id == "encounter_session-1"
    assert fhir_client.encounters["encounter_session-1"].patient_id == "patient-1"
    assert fhir_client.encounters["encounter_session-1"].department_id == "general-medicine"
    assert fhir_client.encounters["encounter_session-1"].status == "planned"
    assert his_client.encounters["encounter_session-1"].patient_id == "patient-1"
    assert his_client.encounters["encounter_session-1"].status == "scheduled"


@pytest.mark.asyncio
async def test_update_encounter_status():
    fhir_client = MockFhirClient()
    his_client = MockHisClient()

    service = HealthcareIntegrationService(
        abdm_client=MockAbdmClient(),
        fhir_client=fhir_client,
        his_client=his_client,
    )

    await service.create_encounter(
        session_id="session-1",
        patient_id="patient-1",
        department_id="general-medicine",
    )

    await service.update_encounter_status(
        "encounter_session-1",
        "in-progress",
    )

    assert fhir_client.encounters["encounter_session-1"].status == "in-progress"
    assert his_client.encounters["encounter_session-1"].status == "in-progress"
