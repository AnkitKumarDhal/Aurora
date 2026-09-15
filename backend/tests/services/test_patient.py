from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.patient import PatientRepository
from backend.domain.patient import Patient
from backend.models.patient import PatientDocument
from backend.services.patient import PatientService


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=PatientRepository)


@pytest.fixture
def service(repository: AsyncMock) -> PatientService:
    return PatientService(repository)


@pytest.fixture
def document() -> PatientDocument:
    timestamp = datetime.now(timezone.utc)

    return PatientDocument(
        patient_id="patient-1",
        display_name="Test Patient",
        date_of_birth=date(1998, 5, 14),
        age=28,
        abha_reference="11-22-33-44-55-66",
        hospital_reference="HOSP-0001",
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_patient(
    service: PatientService,
    repository: AsyncMock,
    document: PatientDocument,
) -> None:
    repository.get_patient.return_value = document

    result = await service.get_patient("patient-1")

    assert result is not None
    assert result.patient_id == "patient-1"
    assert result.display_name == "Test Patient"
    repository.get_patient.assert_awaited_once_with("patient-1")


@pytest.mark.asyncio
async def test_get_patient_missing(
    service: PatientService,
    repository: AsyncMock,
) -> None:
    repository.get_patient.return_value = None

    result = await service.get_patient("missing")

    assert result is None


@pytest.mark.asyncio
async def test_get_by_abha_reference(
    service: PatientService,
    repository: AsyncMock,
    document: PatientDocument,
) -> None:
    repository.get_by_abha_reference.return_value = document

    result = await service.get_by_abha_reference(
        "11-22-33-44-55-66",
    )

    assert result is not None
    assert result.patient_id == "patient-1"


@pytest.mark.asyncio
async def test_get_by_hospital_reference(
    service: PatientService,
    repository: AsyncMock,
    document: PatientDocument,
) -> None:
    repository.get_by_hospital_reference.return_value = document

    result = await service.get_by_hospital_reference(
        "HOSP-0001",
    )

    assert result is not None
    assert result.patient_id == "patient-1"


@pytest.mark.asyncio
async def test_create_patient(
    service: PatientService,
    repository: AsyncMock,
) -> None:
    timestamp = datetime.now(timezone.utc)

    patient = Patient(
        patient_id="patient-1",
        display_name="Test Patient",
        date_of_birth=date(1998, 5, 14),
        age=28,
        abha_reference="11-22-33-44-55-66",
        hospital_reference="HOSP-0001",
        created_at=timestamp,
        updated_at=timestamp,
    )

    result = await service.create_patient(patient)

    assert result is patient
    repository.create_patient.assert_awaited_once()

    document = repository.create_patient.await_args.args[0]

    assert isinstance(document, PatientDocument)
    assert document.patient_id == "patient-1"
