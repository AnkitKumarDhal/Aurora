from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.database.repositories.queue import QueueRepository
from backend.domain.clinical_session import ClinicalSession
from backend.domain.enums import (
    ConsentStatus,
    QueueStatus,
    SessionStatus,
    VerificationStatus,
)
from backend.domain.queue import QueueEntry
from backend.models.clinical_session import ClinicalSessionDocument
from backend.models.queue import QueueEntryDocument
from backend.services.clinical_session import ClinicalSessionService
from backend.services.queue import QueueService
from backend.services.workflow import WorkflowService


@pytest.fixture
def session_repository() -> ClinicalSessionRepository:
    return AsyncMock(spec=ClinicalSessionRepository)


@pytest.fixture
def queue_repository() -> QueueRepository:
    return AsyncMock(spec=QueueRepository)


@pytest.fixture
def session_service(session_repository: ClinicalSessionRepository) -> ClinicalSessionService:
    return ClinicalSessionService(session_repository)


@pytest.fixture
def queue_service(queue_repository: QueueRepository) -> QueueService:
    return QueueService(queue_repository)


@pytest.fixture
def service(
    session_service: ClinicalSessionService,
    queue_service: QueueService,
) -> WorkflowService:
    return WorkflowService(session_service, queue_service)


def make_session(status: SessionStatus) -> ClinicalSession:
    timestamp = datetime.now(timezone.utc)

    return ClinicalSession(
        session_id="session-1",
        patient_id="patient-1",
        department_id="medicine",
        status=status,
        verification_status=VerificationStatus.VERIFIED,
        consent_status=ConsentStatus.GRANTED,
        started_at=timestamp,
        completed_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def make_session_document(status: SessionStatus) -> ClinicalSessionDocument:
    session = make_session(status)

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


def make_queue_entry() -> QueueEntry:
    timestamp = datetime.now(timezone.utc)

    return QueueEntry(
        queue_entry_id="queue-1",
        session_id="session-1",
        department_id="medicine",
        status=QueueStatus.WAITING,
        position=1,
        urgency_level=None,
        priority_score=None,
        doctor_id=None,
        queued_at=timestamp,
        called_at=None,
        completed_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def make_queue_document(status: QueueStatus) -> QueueEntryDocument:
    entry = make_queue_entry()

    return QueueEntryDocument(
        queue_entry_id=entry.queue_entry_id,
        session_id=entry.session_id,
        department_id=entry.department_id,
        status=status,
        position=entry.position,
        urgency_level=entry.urgency_level,
        priority_score=entry.priority_score,
        doctor_id=entry.doctor_id,
        queued_at=entry.queued_at,
        called_at=entry.called_at,
        completed_at=entry.completed_at,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@pytest.mark.asyncio
async def test_queue_session(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.SUMMARY_READY,
    )
    queue_repository.create_entry.return_value = make_queue_document(
        QueueStatus.WAITING,
    )

    result = await service.queue_session(make_queue_entry())

    assert result.session_id == "session-1"
    assert result.status == QueueStatus.WAITING
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_queue_session_requires_summary(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.HISTORY_IN_PROGRESS,
    )

    with pytest.raises(ValueError, match="Session must have a ready summary before queuing"):
        await service.queue_session(make_queue_entry())


@pytest.mark.asyncio
async def test_call_patient(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.ASSIGNED,
    )
    queue_repository.update_entry.return_value = make_queue_document(
        QueueStatus.CALLED,
    )

    result = await service.call_patient("session-1", "queue-1")

    assert result.status == QueueStatus.CALLED
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_call_patient_requires_assignment(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.QUEUED,
    )

    with pytest.raises(ValueError, match="Session must be assigned before calling the patient"):
        await service.call_patient("session-1", "queue-1")


@pytest.mark.asyncio
async def test_start_consultation(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.CALLED,
    )
    queue_repository.update_entry.return_value = make_queue_document(
        QueueStatus.IN_CONSULTATION,
    )

    result = await service.start_consultation("session-1", "queue-1")

    assert result.status == QueueStatus.IN_CONSULTATION
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_consultation_requires_called_state(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.ASSIGNED,
    )

    with pytest.raises(ValueError, match="Session must be called before consultation"):
        await service.start_consultation("session-1", "queue-1")


@pytest.mark.asyncio
async def test_complete_consultation(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.IN_CONSULTATION,
    )
    queue_repository.update_entry.return_value = make_queue_document(
        QueueStatus.COMPLETED,
    )

    result = await service.complete_consultation("session-1", "queue-1")

    assert result.status == QueueStatus.COMPLETED
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_consultation_requires_active_consultation(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.CALLED,
    )

    with pytest.raises(ValueError, match="Session is not in consultation"):
        await service.complete_consultation("session-1", "queue-1")
