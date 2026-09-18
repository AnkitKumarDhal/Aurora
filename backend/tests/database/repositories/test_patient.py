from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.patient import PatientRepository
from backend.models.patient import PatientDocument


@pytest.fixture
def patient() -> PatientDocument:
    now = datetime.now(timezone.utc)

    return PatientDocument(
        patient_id="patient-001",
        display_name="Test Patient",
        date_of_birth=date(2000, 1, 1),
        age=26,
        abha_reference="abha-001",
        aadhaar_reference="123456789012",
        hospital_reference="mrn-001",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def repository() -> PatientRepository:
    repository = PatientRepository()
    repository.collection = AsyncMock()
    return repository


def test_patient_document_serializes_dates_for_mongodb(
    patient: PatientDocument,
) -> None:
    document = patient.to_mongo()

    assert isinstance(document["date_of_birth"], datetime)
    assert document["date_of_birth"] == datetime(
        2000,
        1,
        1,
        tzinfo=timezone.utc,
    )
    assert isinstance(document["created_at"], datetime)
    assert isinstance(document["updated_at"], datetime)


def test_patient_document_round_trips_date_of_birth(
    patient: PatientDocument,
) -> None:
    document = patient.to_mongo()
    restored = PatientDocument.from_mongo(document)

    assert restored.date_of_birth == date(2000, 1, 1)


@pytest.mark.asyncio
async def test_get_patient(
    repository: PatientRepository,
    patient: PatientDocument,
) -> None:
    repository.collection.find_one.return_value = patient.to_mongo()

    result = await repository.get_patient("patient-001")

    assert result is not None
    assert result.patient_id == "patient-001"
    assert result.date_of_birth == date(2000, 1, 1)

    repository.collection.find_one.assert_awaited_once_with(
        {"patient_id": "patient-001"},
    )


@pytest.mark.asyncio
async def test_get_by_abha_reference(
    repository: PatientRepository,
    patient: PatientDocument,
) -> None:
    repository.collection.find_one.return_value = patient.to_mongo()

    result = await repository.get_by_abha_reference("abha-001")

    assert result is not None
    assert result.abha_reference == "abha-001"

    repository.collection.find_one.assert_awaited_once_with(
        {"abha_reference": "abha-001"},
    )


@pytest.mark.asyncio
async def test_get_by_aadhaar_reference(
    repository: PatientRepository,
    patient: PatientDocument,
) -> None:
    repository.collection.find_one.return_value = patient.to_mongo()

    result = await repository.get_by_aadhaar_reference("123456789012")

    assert result is not None
    assert result.aadhaar_reference == "123456789012"

    repository.collection.find_one.assert_awaited_once_with(
        {"aadhaar_reference": "123456789012"},
    )


@pytest.mark.asyncio
async def test_get_by_hospital_reference(
    repository: PatientRepository,
    patient: PatientDocument,
) -> None:
    repository.collection.find_one.return_value = patient.to_mongo()

    result = await repository.get_by_hospital_reference("mrn-001")

    assert result is not None
    assert result.hospital_reference == "mrn-001"

    repository.collection.find_one.assert_awaited_once_with(
        {"hospital_reference": "mrn-001"},
    )
