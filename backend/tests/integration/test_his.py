import pytest

from backend.integrations.his import HisEncounter, HisPatient, MockHisClient


@pytest.mark.asyncio
async def test_upsert_patient():
    client = MockHisClient()
    patient = HisPatient(
        patient_id="patient-1",
        hospital_reference="HOSP-0001",
        display_name="Demo Patient",
        date_of_birth="1998-05-14",
    )

    result = await client.upsert_patient(patient)

    assert result is patient
    assert client.patients["patient-1"] == patient


@pytest.mark.asyncio
async def test_create_encounter():
    client = MockHisClient()
    encounter = HisEncounter(
        encounter_id="encounter-1",
        patient_id="patient-1",
        department_id="general-medicine",
        status="scheduled",
    )

    result = await client.create_encounter(encounter)

    assert result is encounter
    assert client.encounters["encounter-1"] == encounter


@pytest.mark.asyncio
async def test_update_encounter_status():
    client = MockHisClient()
    encounter = HisEncounter(
        encounter_id="encounter-1",
        patient_id="patient-1",
        department_id="general-medicine",
        status="scheduled",
    )

    await client.create_encounter(encounter)
    result = await client.update_encounter_status("encounter-1", "in-progress")

    assert result is encounter
    assert result.status == "in-progress"


@pytest.mark.asyncio
async def test_update_missing_encounter_status():
    client = MockHisClient()

    result = await client.update_encounter_status("missing", "completed")

    assert result is None
