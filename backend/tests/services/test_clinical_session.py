from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.domain.clinical_session import ClinicalSession
from backend.domain.enums import (
    ConsentStatus,
    SessionStatus,
    VerificationStatus,
)
from backend.models.clinical_session import ClinicalSessionDocument
from backend.services.clinical_session import ClinicalSessionService


def make_session() -> ClinicalSession:
    now = datetime.now(timezone.utc)

    return ClinicalSession(
        session_id="session-1",
        patient_id="patient-1",
        department_id="general-medicine",
        status=SessionStatus.CREATED,
        verification_status=VerificationStatus.PENDING,
        consent_status=ConsentStatus.PENDING,
        created_at=now,
        updated_at=now,
    )


def make_document(session: ClinicalSession) -> ClinicalSessionDocument:
    return ClinicalSessionDocument(
        session_id=session.session_id,
        patient_id=session.patient_id,
        department_id=session.department_id,
        status=session.status,
        verification_status=session.verification_status,
        consent_status=session.consent_status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=ClinicalSessionRepository)


@pytest.fixture
def service(repository: AsyncMock) -> ClinicalSessionService:
    return ClinicalSessionService(repository)


@pytest.mark.asyncio
async def test_create_session(service: ClinicalSessionService, repository: AsyncMock) -> None:
    session = make_session()
    result = await service.create_session(session)
    assert result == session
    repository.create_session.assert_awaited_once()
    document = repository.create_session.await_args.args[0]
    assert isinstance(document, ClinicalSessionDocument)
    assert document.session_id == "session-1"
    assert document.patient_id == "patient-1"
    assert document.department_id == "general-medicine"
    assert document.status == SessionStatus.CREATED


@pytest.mark.asyncio
async def test_get_session(service: ClinicalSessionService, repository: AsyncMock,) -> None:
    session = make_session()
    repository.get_session.return_value = make_document(session)
    result = await service.get_session("session-1")
    assert result is not None
    assert result.session_id == session.session_id
    assert result.patient_id == session.patient_id
    assert result.department_id == session.department_id
    assert result.status == SessionStatus.CREATED
    repository.get_session.assert_awaited_once_with("session-1")


@pytest.mark.asyncio
async def test_get_session_returns_none_when_missing(service: ClinicalSessionService, repository: AsyncMock,) -> None:
    repository.get_session.return_value = None
    result = await service.get_session("missing-session")
    assert result is None
    repository.get_session.assert_awaited_once_with("missing-session")


@pytest.mark.asyncio
async def test_transition_session(service: ClinicalSessionService, repository: AsyncMock,) -> None:
    session = make_session()
    repository.get_session.return_value = make_document(session)
    result = await service.transition_session("session-1", SessionStatus.IDENTIFYING)
    assert result is not None
    assert result.status == SessionStatus.IDENTIFYING
    assert result.started_at is not None
    repository.update_session.assert_awaited_once()
    session_id, updates = repository.update_session.await_args.args
    assert session_id == "session-1"
    assert updates["status"] == SessionStatus.IDENTIFYING
    assert updates["started_at"] is not None


@pytest.mark.asyncio
async def test_transition_session_returns_none_when_missing(service: ClinicalSessionService, repository: AsyncMock,) -> None:
    repository.get_session.return_value = None
    result = await service.transition_session("missing-session", SessionStatus.IDENTIFYING)
    assert result is None
    repository.update_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_transition_session_rejects_invalid_transition(service: ClinicalSessionService, repository: AsyncMock,) -> None:
    session = make_session()
    repository.get_session.return_value = make_document(session)
    with pytest.raises(ValueError, match="Invalid clinical session transition"):
        await service.transition_session("session-1", SessionStatus.IN_CONSULTATION)
    repository.update_session.assert_not_awaited()
