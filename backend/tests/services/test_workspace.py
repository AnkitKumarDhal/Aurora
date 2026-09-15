from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.assignment import AssignmentRepository
from backend.database.repositories.clinical_session import ClinicalSessionRepository
from backend.database.repositories.doctor import DoctorRepository
from backend.database.repositories.queue import QueueRepository
from backend.domain.assignment import DoctorAssignment
from backend.domain.clinical_session import ClinicalSession
from backend.domain.enums import (
    AssignmentStatus,
    ConsentStatus,
    QueueStatus,
    SessionStatus,
    VerificationStatus,
)
from backend.domain.queue import QueueEntry
from backend.models.assignment import DoctorAssignmentDocument
from backend.models.clinical_session import ClinicalSessionDocument
from backend.models.queue import QueueEntryDocument
from backend.services.assignment import AssignmentService
from backend.services.assignment_scheduler import AssignmentSchedulerService
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
def assignment_repository() -> AssignmentRepository:
    return AsyncMock(spec=AssignmentRepository)


@pytest.fixture
def doctor_repository() -> DoctorRepository:
    return AsyncMock(spec=DoctorRepository)


@pytest.fixture
def session_service(session_repository: ClinicalSessionRepository) -> ClinicalSessionService:
    return ClinicalSessionService(session_repository)


@pytest.fixture
def queue_service(queue_repository: QueueRepository) -> QueueService:
    return QueueService(queue_repository)


@pytest.fixture
def assignment_service(assignment_repository: AssignmentRepository) -> AssignmentService:
    return AssignmentService(assignment_repository)


@pytest.fixture
def assignment_scheduler(
    doctor_repository: DoctorRepository,
    assignment_repository: AssignmentRepository,
    assignment_service: AssignmentService,
) -> AssignmentSchedulerService:
    return AssignmentSchedulerService(
        doctor_repository,
        assignment_repository,
        assignment_service,
    )


@pytest.fixture
def service(
    session_service: ClinicalSessionService,
    queue_service: QueueService,
    assignment_scheduler: AssignmentSchedulerService,
) -> WorkflowService:
    return WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
    )


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


def make_queue_entry(status: QueueStatus = QueueStatus.WAITING) -> QueueEntry:
    timestamp = datetime.now(timezone.utc)

    return QueueEntry(
        queue_entry_id="queue-1",
        session_id="session-1",
        department_id="medicine",
        status=status,
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
    entry = make_queue_entry(status)

    return QueueEntryDocument(
        queue_entry_id=entry.queue_entry_id,
        session_id=entry.session_id,
        department_id=entry.department_id,
        status=entry.status,
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


def make_assignment() -> DoctorAssignment:
    timestamp = datetime.now(timezone.utc)

    return DoctorAssignment(
        assignment_id="assignment-1",
        session_id="session-1",
        doctor_id="doctor-1",
        department_id="medicine",
        status=AssignmentStatus.ACTIVE,
        assigned_at=timestamp,
        released_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def make_assignment_document() -> DoctorAssignmentDocument:
    assignment = make_assignment()

    return DoctorAssignmentDocument(
        assignment_id=assignment.assignment_id,
        session_id=assignment.session_id,
        doctor_id=assignment.doctor_id,
        department_id=assignment.department_id,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        released_at=assignment.released_at,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
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

    assert result.status == QueueStatus.WAITING
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_patient(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
    assignment_repository: AssignmentRepository,
    doctor_repository: DoctorRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.QUEUED,
    )
    queue_repository.get_entry.return_value = make_queue_document(
        QueueStatus.WAITING,
    )
    queue_repository.update_entry.return_value = make_queue_document(
        QueueStatus.WAITING,
    )
    doctor_repository.get_department_doctors.return_value = []
    assignment_repository.get_doctor_assignments.return_value = []

    service.assignment_scheduler.assign = AsyncMock(
        return_value=make_assignment())

    result = await service.assign_patient("session-1", "queue-1")

    assert result is not None
    assert result.doctor_id == "doctor-1"
    queue_repository.update_entry.assert_awaited_once_with(
        "queue-1",
        {"doctor_id": "doctor-1"},
    )
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_patient_returns_none_when_no_doctor(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.QUEUED,
    )
    queue_repository.get_entry.return_value = make_queue_document(
        QueueStatus.WAITING,
    )

    service.assignment_scheduler.assign = AsyncMock(return_value=None)

    result = await service.assign_patient("session-1", "queue-1")

    assert result is None
    queue_repository.update_entry.assert_not_awaited()
    session_repository.update_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_patient_requires_queued_session(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.SUMMARY_READY,
    )

    with pytest.raises(ValueError, match="Session must be queued before assignment"):
        await service.assign_patient("session-1", "queue-1")


@pytest.mark.asyncio
async def test_assign_patient_rejects_wrong_session(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.QUEUED,
    )

    entry = make_queue_entry()
    entry.session_id = "other-session"

    queue_repository.get_entry.return_value = QueueEntryDocument(
        queue_entry_id=entry.queue_entry_id,
        session_id=entry.session_id,
        department_id=entry.department_id,
        status=entry.status,
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

    with pytest.raises(ValueError, match="Queue entry does not belong to session"):
        await service.assign_patient("session-1", "queue-1")


@pytest.mark.asyncio
async def test_call_patient(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.ASSIGNED,
    )

    entry = make_queue_entry()
    entry.doctor_id = "doctor-1"

    queue_repository.get_entry.return_value = QueueEntryDocument(
        queue_entry_id=entry.queue_entry_id,
        session_id=entry.session_id,
        department_id=entry.department_id,
        status=entry.status,
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
    queue_repository.update_entry.return_value = make_queue_document(
        QueueStatus.CALLED,
    )

    result = await service.call_patient("session-1", "queue-1")

    assert result.status == QueueStatus.CALLED
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_call_patient_requires_assigned_doctor(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.ASSIGNED,
    )
    queue_repository.get_entry.return_value = make_queue_document(
        QueueStatus.WAITING,
    )

    with pytest.raises(ValueError, match="Queue entry has no assigned doctor"):
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
    queue_repository.get_entry.return_value = make_queue_document(
        QueueStatus.CALLED,
    )
    queue_repository.update_entry.return_value = make_queue_document(
        QueueStatus.IN_CONSULTATION,
    )

    result = await service.start_consultation("session-1", "queue-1")

    assert result.status == QueueStatus.IN_CONSULTATION
    session_repository.update_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_consultation(
    service: WorkflowService,
    session_repository: ClinicalSessionRepository,
    queue_repository: QueueRepository,
) -> None:
    session_repository.get_session.return_value = make_session_document(
        SessionStatus.IN_CONSULTATION,
    )
    queue_repository.get_entry.return_value = make_queue_document(
        QueueStatus.IN_CONSULTATION,
    )
    queue_repository.update_entry.return_value = make_queue_document(
        QueueStatus.COMPLETED,
    )

    result = await service.complete_consultation("session-1", "queue-1")

    assert result.status == QueueStatus.COMPLETED
    session_repository.update_session.assert_awaited_once()
