from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest

from database.repositories.patient import PatientRepository
from models.patient import PatientDocument


@pytest.fixture
def patient() -> PatientDocument:
    now = datetime.now(timezone.utc)

    return PatientDocument(
        patient_id="patient-001",
        display_name="Test Patient",
        date_of_birth=date(2000, 1, 1),
        age=26,
        abha_reference="abha-001",
        hospital_reference="mrn-001",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def repository() -> PatientRepository:
    repository = PatientRepository()
    repository.collection = AsyncMock()
    return repository


@pytest.mark.asyncio
async def test_get_patient(repository: PatientRepository, patient: PatientDocument,) -> None:
    repository.collection.find_one.return_value = patient.to_mongo()
    result = await repository.get_patient("patient-001")
    assert result is not None
    assert result.patient_id == "patient-001"
    repository.collection.find_one.assert_awaited_once_with(
        {"patient_id": "patient-001"},)


@pytest.mark.asyncio
async def test_get_by_abha_reference(repository: PatientRepository, patient: PatientDocument,) -> None:
    repository.collection.find_one.return_value = patient.to_mongo()
    result = await repository.get_by_abha_reference("abha-001")
    assert result is not None
    assert result.abha_reference == "abha-001"
    repository.collection.find_one.assert_awaited_once_with(
        {"abha_reference": "abha-001"},)


@pytest.mark.asyncio
async def test_get_by_hospital_reference(repository: PatientRepository, patient: PatientDocument,) -> None:
    repository.collection.find_one.return_value = patient.to_mongo()
    result = await repository.get_by_hospital_reference("mrn-001")
    assert result is not None
    assert result.hospital_reference == "mrn-001"
    repository.collection.find_one.assert_awaited_once_with(
        {"hospital_reference": "mrn-001"},)
