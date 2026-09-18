from unittest.mock import AsyncMock

import pytest

from backend.domain.enums import SessionStatus, VerificationStatus
from backend.integrations.identity import (
    IdentityVerificationResult,
    MockIdentityProvider,
)
from backend.services.verification import VerificationService


@pytest.mark.asyncio
async def test_verify_known_identity() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    patient_service.get_by_abha_reference.return_value = None
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.CREATED
    identifying_session = AsyncMock()
    identifying_session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session
    session_service.transition_session.return_value = identifying_session
    session_service.set_identity.return_value = identifying_session

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    verification_id, result = await service.verify(
        "session-1",
        "ABHA",
        "1111-2222-3333-44",
    )

    assert verification_id.startswith("ver_")
    assert result.status == VerificationStatus.VERIFIED
    assert result.patient_id == "patient-demo-001"
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.IDENTIFYING,
    )
    session_service.set_identity.assert_awaited_once_with(
        "session-1",
        "patient-demo-001",
        VerificationStatus.VERIFIED,
    )
    patient_service.create_patient.assert_awaited_once()
    healthcare_integration_service.sync_patient.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_existing_identity_syncs_patient() -> None:
    session_service = AsyncMock()
    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session

    existing_patient = AsyncMock()
    existing_patient.patient_id = "patient-demo-001"
    patient_service.get_by_abha_reference.return_value = existing_patient

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    verification_id, result = await service.verify(
        "session-1",
        "ABHA",
        "1111-2222-3333-00",
    )

    assert verification_id.startswith("ver_")
    assert result.status == VerificationStatus.VERIFIED
    assert result.patient_id == "patient-demo-001"
    patient_service.create_patient.assert_not_awaited()
    healthcare_integration_service.sync_patient.assert_awaited_once_with(
        existing_patient,
    )
    session_service.set_identity.assert_awaited_once_with(
        "session-1",
        "patient-demo-001",
        VerificationStatus.VERIFIED,
    )


@pytest.mark.asyncio
async def test_verify_unknown_identity() -> None:
    session_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session

    patient_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    service = VerificationService(
        session_service=session_service,
        patient_service=patient_service,
        identity_provider=MockIdentityProvider(),
        healthcare_integration_service=healthcare_integration_service,
    )

    verification_id, result = await service.verify(
        "session-1",
        "ABHA",
        "0000-0000-0000-00",
    )

    assert verification_id.startswith("ver_")
    assert result.status == VerificationStatus.FAILED
    assert result.patient_id is None
    session_service.set_identity.assert_not_awaited()
    patient_service.create_patient.assert_not_awaited()
    healthcare_integration_service.sync_patient.assert_not_awaited()


@pytest.mark.asyncio
async def test_mock_identity_rejects_unknown_method() -> None:
    result = await MockIdentityProvider().verify(
        "HOSPITAL_ID",
        "1111-2222-3333",
    )

    assert result == IdentityVerificationResult(
        status=VerificationStatus.FAILED,
    )
