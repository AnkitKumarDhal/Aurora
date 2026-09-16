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
