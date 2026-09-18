from datetime import datetime, timezone
from unittest.mock import AsyncMock

from pymongo.errors import DuplicateKeyError
import pytest

from backend.domain.enums import SessionStatus, VerificationStatus
from backend.domain.patient import Patient
from backend.integrations.identity import MockIdentityProvider
from backend.services.verification import VerificationService


@pytest.mark.asyncio
async def test_verify_known_new_identity() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.CREATED

    identifying_session = AsyncMock()
    identifying_session.status = SessionStatus.IDENTIFYING

    verified_session = AsyncMock()
    verified_session.status = SessionStatus.IDENTIFYING

    session_service.get_session.return_value = session
    session_service.transition_session.return_value = identifying_session
    session_service.set_verification_status.return_value = verified_session

    patient_service.get_by_identity.return_value = None
    patient_service.get_patient.return_value = None

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    verification_id, result, existing_patient = await service.verify(
        "session-1",
        "ABHA",
        "11112222333344",
    )

    assert verification_id.startswith("ver_")
    assert result.status == VerificationStatus.VERIFIED
    assert result.patient_id == "patient-demo-001"
    assert existing_patient is None

    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.IDENTIFYING,
    )
    session_service.set_verification_status.assert_awaited_once_with(
        "session-1",
        VerificationStatus.VERIFIED,
    )
    patient_service.create_patient.assert_not_awaited()
    healthcare_integration_service.sync_patient.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_existing_identity() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session

    existing_patient = AsyncMock()
    existing_patient.patient_id = "patient-demo-001"
    patient_service.get_by_identity.return_value = existing_patient
    session_service.set_verification_status.return_value = session

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    verification_id, result, found_patient = await service.verify(
        "session-1",
        "ABHA",
        "1111-2222-3333-44",
    )

    assert verification_id.startswith("ver_")
    assert result.status == VerificationStatus.VERIFIED
    assert result.patient_id == "patient-demo-001"
    assert found_patient is existing_patient

    patient_service.create_patient.assert_not_awaited()
    healthcare_integration_service.sync_patient.assert_not_awaited()
    session_service.set_identity.assert_not_awaited()
    session_service.set_verification_status.assert_awaited_once_with(
        "session-1",
        VerificationStatus.VERIFIED,
    )


@pytest.mark.asyncio
async def test_verify_unknown_identity() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    verification_id, result, existing_patient = await service.verify(
        "session-1",
        "ABHA",
        "00000000000000",
    )

    assert verification_id.startswith("ver_")
    assert result.status == VerificationStatus.FAILED
    assert result.patient_id is None
    assert existing_patient is None

    session_service.set_verification_status.assert_not_awaited()
    patient_service.create_patient.assert_not_awaited()
    healthcare_integration_service.sync_patient.assert_not_awaited()


@pytest.mark.asyncio
async def test_persist_identity_creates_first_visit_patient() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session
    session_service.set_identity.return_value = session

    patient_service.get_by_identity.return_value = None
    patient_service.get_patient.return_value = None

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    patient = await service.persist_identity(
        "session-1",
        "ABHA",
        "1111-2222-3333-44",
    )

    assert isinstance(patient, Patient)
    assert patient.patient_id == "patient-demo-001"
    assert patient.display_name == "Demo Patient"
    assert patient.abha_reference == "11112222333344"
    assert patient.storage_consent_granted_at is not None

    patient_service.get_by_identity.assert_awaited_once_with(
        "ABHA",
        "1111-2222-3333-44",
    )
    patient_service.get_patient.assert_awaited_once_with(
        "patient-demo-001",
    )
    patient_service.create_patient.assert_awaited_once_with(patient)
    patient_service.update_patient.assert_not_awaited()

    healthcare_integration_service.sync_patient.assert_awaited_once_with(
        patient,
    )
    session_service.set_identity.assert_awaited_once_with(
        "session-1",
        "patient-demo-001",
        VerificationStatus.VERIFIED,
    )


@pytest.mark.asyncio
async def test_persist_identity_reuses_returning_patient() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session
    session_service.set_identity.return_value = session

    existing_patient = Patient(
        patient_id="patient-demo-001",
        display_name="Demo Patient",
        abha_reference="11112222333344",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    patient_service.get_by_identity.return_value = existing_patient
    patient_service.update_patient.return_value = existing_patient

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    patient = await service.persist_identity(
        "session-1",
        "ABHA",
        "1111-2222-3333-44",
    )

    assert patient is existing_patient

    patient_service.get_by_identity.assert_awaited_once_with(
        "ABHA",
        "1111-2222-3333-44",
    )
    patient_service.get_patient.assert_not_awaited()
    patient_service.create_patient.assert_not_awaited()
    patient_service.update_patient.assert_awaited_once()

    update_args = patient_service.update_patient.await_args.args

    assert update_args[0] == "patient-demo-001"
    assert update_args[1]["abha_reference"] == "11112222333344"
    assert update_args[1]["storage_consent_granted_at"] is not None

    healthcare_integration_service.sync_patient.assert_awaited_once_with(
        existing_patient,
    )
    session_service.set_identity.assert_awaited_once_with(
        "session-1",
        "patient-demo-001",
        VerificationStatus.VERIFIED,
    )


@pytest.mark.asyncio
async def test_mock_identity_accepts_aadhaar() -> None:
    result = await MockIdentityProvider().verify(
        "AADHAAR",
        "1234-5678-9012",
    )

    assert result.status == VerificationStatus.VERIFIED
    assert result.patient_id == "patient-demo-001"


@pytest.mark.asyncio
async def test_mock_identity_rejects_unknown_method() -> None:
    result = await MockIdentityProvider().verify(
        "HOSPITAL_ID",
        "11112222333344",
    )

    assert result.status == VerificationStatus.FAILED


@pytest.mark.asyncio
async def test_persist_identity_recovers_from_duplicate_patient_creation() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session
    session_service.set_identity.return_value = session

    existing_patient = Patient(
        patient_id="patient-demo-001",
        display_name="Demo Patient",
        abha_reference="11112222333344",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    patient_service.get_by_identity.side_effect = [
        None,
        existing_patient,
    ]
    patient_service.get_patient.return_value = None
    patient_service.create_patient.side_effect = DuplicateKeyError(
        "duplicate patient",
    )
    patient_service.update_patient.return_value = existing_patient

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    patient = await service.persist_identity(
        "session-1",
        "ABHA",
        "1111-2222-3333-44",
    )

    assert patient is existing_patient
    patient_service.create_patient.assert_awaited_once()
    patient_service.update_patient.assert_awaited_once()
    healthcare_integration_service.sync_patient.assert_awaited_once_with(
        existing_patient,
    )
    session_service.set_identity.assert_awaited_once_with(
        "session-1",
        "patient-demo-001",
        VerificationStatus.VERIFIED,
    )
