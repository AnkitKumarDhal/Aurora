from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.domain.enums import (
    AssignmentStatus,
    QueueStatus,
    SessionStatus,
    UrgencyLevel,
)
from backend.services.workflow import WorkflowService


def make_session(status: SessionStatus):
    return type(
        "Session",
        (),
        {
            "session_id": "session-1",
            "patient_id": "patient-1",
            "department_id": "general-medicine",
            "status": status,
        },
    )()


def make_triage():
    return type(
        "Triage",
        (),
        {
            "triage_id": "triage-1",
            "urgency_level": UrgencyLevel.LEVEL_4,
            "priority_score": 80,
        },
    )()


def make_assignment():
    timestamp = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "session-1",
            "doctor_id": "doctor-1",
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": timestamp,
            "released_at": None,
        },
    )()


def make_queue_entry(
    status: QueueStatus = QueueStatus.WAITING,
    doctor_id: str | None = None,
):
    timestamp = datetime.now(timezone.utc)

    return type(
        "QueueEntry",
        (),
        {
            "queue_entry_id": "queue-1",
            "session_id": "session-1",
            "department_id": "general-medicine",
            "status": status,
            "urgency_level": UrgencyLevel.LEVEL_4,
            "priority_score": 80,
            "doctor_id": doctor_id,
            "position": 1,
            "queued_at": timestamp,
            "called_at": None,
            "completed_at": None,
        },
    )()


@pytest.mark.asyncio
async def test_queue_session_from_triage():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.SUMMARY_READY,
    )
    triage_service.get_session_result.return_value = make_triage()
    queue_service.enqueue.return_value = make_queue_entry()

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    result = await service.queue_session_from_triage("session-1")

    assert result.queue_entry_id == "queue-1"
    queue_service.enqueue.assert_awaited_once()
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.QUEUED,
    )
    healthcare_integration_service.create_encounter.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_patient_uses_scheduler_and_creates_encounter():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.QUEUED,
    )
    queue_service.get_entry.return_value = make_queue_entry()
    assignment_scheduler.assign.return_value = make_assignment()

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    result = await service.assign_patient(
        "session-1",
        "queue-1",
    )

    assert result.doctor_id == "doctor-1"
    queue_service.update_entry.assert_awaited_once()
    healthcare_integration_service.create_encounter.assert_awaited_once_with(
        session_id="session-1",
        patient_id="patient-1",
        department_id="general-medicine",
    )
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.ASSIGNED,
    )


@pytest.mark.asyncio
async def test_assign_patient_returns_none_when_no_doctor_available():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.QUEUED,
    )
    queue_service.get_entry.return_value = make_queue_entry()
    assignment_scheduler.assign.return_value = None

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    result = await service.assign_patient(
        "session-1",
        "queue-1",
    )

    assert result is None
    session_service.transition_session.assert_not_awaited()
    healthcare_integration_service.create_encounter.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_patient_rejects_already_assigned_entry():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.QUEUED,
    )
    queue_service.get_entry.return_value = make_queue_entry(
        doctor_id="doctor-1",
    )

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    with pytest.raises(ValueError, match="Queue entry is already assigned"):
        await service.assign_patient(
            "session-1",
            "queue-1",
        )

    assignment_scheduler.assign.assert_not_awaited()
    queue_service.update_entry.assert_not_awaited()
    healthcare_integration_service.create_encounter.assert_not_awaited()
    session_service.transition_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_call_patient_updates_encounter_status():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.ASSIGNED,
    )
    queue_service.get_entry.return_value = make_queue_entry(
        doctor_id="doctor-1",
    )
    queue_service.mark_called.return_value = make_queue_entry(
        status=QueueStatus.CALLED,
        doctor_id="doctor-1",
    )

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    result = await service.call_patient(
        "session-1",
        "queue-1",
        "doctor-1",
    )

    assert result.status == QueueStatus.CALLED
    healthcare_integration_service.update_encounter_status.assert_awaited_once_with(
        "encounter_session-1",
        "arrived",
    )
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.CALLED,
    )


@pytest.mark.asyncio
async def test_start_consultation_updates_encounter_status():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.CALLED,
    )
    queue_service.get_entry.return_value = make_queue_entry(
        status=QueueStatus.CALLED,
        doctor_id="doctor-1",
    )
    queue_service.start_consultation.return_value = make_queue_entry(
        status=QueueStatus.IN_CONSULTATION,
        doctor_id="doctor-1",
    )

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    result = await service.start_consultation(
        "session-1",
        "queue-1",
        "doctor-1",
    )

    assert result.status == QueueStatus.IN_CONSULTATION
    healthcare_integration_service.update_encounter_status.assert_awaited_once_with(
        "encounter_session-1",
        "in-progress",
    )
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.IN_CONSULTATION,
    )


@pytest.mark.asyncio
async def test_complete_consultation_updates_encounter_status():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.IN_CONSULTATION,
    )
    queue_service.get_entry.return_value = make_queue_entry(
        status=QueueStatus.IN_CONSULTATION,
        doctor_id="doctor-1",
    )
    assignment_service.get_session_assignment.return_value = make_assignment()
    queue_service.complete.return_value = make_queue_entry(
        status=QueueStatus.COMPLETED,
        doctor_id="doctor-1",
    )
    assignment_service.release_assignment.return_value = make_assignment()

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    result = await service.complete_consultation(
        "session-1",
        "queue-1",
        "doctor-1",
    )

    assert result.status == QueueStatus.COMPLETED
    healthcare_integration_service.update_encounter_status.assert_awaited_once_with(
        "encounter_session-1",
        "finished",
    )
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.COMPLETED,
    )


@pytest.mark.asyncio
async def test_complete_workflow_lifecycle():
    session_service = AsyncMock()
    queue_service = AsyncMock()
    assignment_scheduler = AsyncMock()
    assignment_service = AsyncMock()
    triage_service = AsyncMock()
    healthcare_integration_service = AsyncMock()

    session = make_session(SessionStatus.SUMMARY_READY)
    triage = make_triage()
    queue_entry = None
    assignment = make_assignment()

    async def get_session(session_id: str):
        assert session_id == "session-1"
        return session

    async def transition_session(
        session_id: str,
        status: SessionStatus,
    ):
        assert session_id == "session-1"
        session.status = status
        return session

    async def enqueue(entry):
        nonlocal queue_entry
        queue_entry = entry
        queue_entry.position = 1
        queue_entry.queued_at = datetime.now(timezone.utc)
        return queue_entry

    async def get_entry(queue_entry_id: str):
        assert queue_entry_id == "queue-1"
        return queue_entry

    async def update_entry(
        queue_entry_id: str,
        updates: dict,
    ):
        assert queue_entry_id == "queue-1"

        for key, value in updates.items():
            setattr(queue_entry, key, value)

        return queue_entry

    async def mark_called(queue_entry_id: str):
        assert queue_entry_id == "queue-1"
        queue_entry.status = QueueStatus.CALLED
        queue_entry.called_at = datetime.now(timezone.utc)
        return queue_entry

    async def start_consultation(queue_entry_id: str):
        assert queue_entry_id == "queue-1"
        queue_entry.status = QueueStatus.IN_CONSULTATION
        return queue_entry

    async def complete(queue_entry_id: str):
        assert queue_entry_id == "queue-1"
        queue_entry.status = QueueStatus.COMPLETED
        queue_entry.completed_at = datetime.now(timezone.utc)
        return queue_entry

    async def get_session_result(session_id: str):
        assert session_id == "session-1"
        return triage

    async def get_session_assignment(session_id: str):
        assert session_id == "session-1"
        return assignment

    async def create_assignment(value):
        assert value.assignment_id == assignment.assignment_id
        return value

    async def release_assignment(assignment_id: str):
        assert assignment_id == assignment.assignment_id
        assignment.status = AssignmentStatus.RELEASED
        assignment.released_at = datetime.now(timezone.utc)
        return assignment

    session_service.get_session.side_effect = get_session
    session_service.transition_session.side_effect = transition_session

    triage_service.get_session_result.side_effect = get_session_result

    queue_service.enqueue.side_effect = enqueue
    queue_service.get_entry.side_effect = get_entry
    queue_service.update_entry.side_effect = update_entry
    queue_service.mark_called.side_effect = mark_called
    queue_service.start_consultation.side_effect = start_consultation
    queue_service.complete.side_effect = complete

    assignment_scheduler.assign.return_value = assignment
    assignment_service.create_assignment.side_effect = create_assignment
    assignment_service.get_session_assignment.side_effect = get_session_assignment
    assignment_service.release_assignment.side_effect = release_assignment

    service = WorkflowService(
        session_service,
        queue_service,
        assignment_scheduler,
        assignment_service,
        triage_service,
        healthcare_integration_service,
    )

    queued_entry = await service.queue_session_from_triage("session-1")

    assert queued_entry.status == QueueStatus.WAITING
    assert queued_entry.position == 1
    assert session.status == SessionStatus.QUEUED

    assigned_doctor = await service.assign_patient(
        "session-1",
        "queue-1",
    )

    assert assigned_doctor.doctor_id == "doctor-1"
    assert queue_entry.doctor_id == "doctor-1"
    assert session.status == SessionStatus.ASSIGNED

    called_entry = await service.call_patient(
        "session-1",
        "queue-1",
        "doctor-1",
    )

    assert called_entry.status == QueueStatus.CALLED
    assert session.status == SessionStatus.CALLED

    consultation_entry = await service.start_consultation(
        "session-1",
        "queue-1",
        "doctor-1",
    )

    assert consultation_entry.status == QueueStatus.IN_CONSULTATION
    assert session.status == SessionStatus.IN_CONSULTATION

    completed_entry = await service.complete_consultation(
        "session-1",
        "queue-1",
        "doctor-1",
    )

    assert completed_entry.status == QueueStatus.COMPLETED
    assert session.status == SessionStatus.COMPLETED
    assert assignment.status == AssignmentStatus.RELEASED
    assert healthcare_integration_service.create_encounter.await_count == 1
    assert healthcare_integration_service.update_encounter_status.await_count == 3
