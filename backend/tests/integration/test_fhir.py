import pytest

from backend.integrations.fhir import FhirDocumentReference, FhirEncounter, FhirPatient, MockFhirClient


@pytest.mark.asyncio
async def test_upsert_patient():
    client = MockFhirClient()

    patient = FhirPatient(
        patient_id="patient-1",
        abha_id="11-22-33-44-55-66",
        display_name="Demo Patient",
        date_of_birth="1998-05-14",
    )

    result = await client.upsert_patient(patient)

    assert result is patient
    assert client.patients["patient-1"] == patient


@pytest.mark.asyncio
async def test_create_encounter():
    client = MockFhirClient()

    encounter = FhirEncounter(
        encounter_id="encounter-1",
        patient_id="patient-1",
        department_id="general-medicine",
        status="in-progress",
    )

    result = await client.create_encounter(encounter)

    assert result is encounter
    assert client.encounters["encounter-1"] == encounter


@pytest.mark.asyncio
async def test_create_document_reference():
    client = MockFhirClient()

    document = FhirDocumentReference(
        document_reference_id="document-reference-1",
        patient_id="patient-1",
        document_id="doc-1",
        document_type="LAB_REPORT",
        title="Blood Report",
    )

    result = await client.create_document_reference(document)

    assert result is document
    assert client.documents["document-reference-1"] == document
