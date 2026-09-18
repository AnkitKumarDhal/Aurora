from unittest.mock import AsyncMock

import pytest

from backend.domain.enums import SessionStatus, VerificationStatus
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
