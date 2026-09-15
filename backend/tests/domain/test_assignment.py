from datetime import datetime, timezone

from backend.domain.assignment import DoctorAssignment
from backend.domain.enums import AssignmentStatus


def test_assignment_defaults_to_active():
    assignment = DoctorAssignment(
        assignment_id="assignment-001",
        session_id="session-001",
        doctor_id="doctor-001",
        department_id="general-medicine",
    )

    assert assignment.status == AssignmentStatus.ACTIVE
    assert assignment.assigned_at is None
    assert assignment.released_at is None


def test_assignment_accepts_assigned_timestamp():
    timestamp = datetime.now(timezone.utc)

    assignment = DoctorAssignment(
        assignment_id="assignment-001",
        session_id="session-001",
        doctor_id="doctor-001",
        department_id="general-medicine",
        assigned_at=timestamp,
    )

    assert assignment.assigned_at == timestamp


def test_assignment_can_be_completed():
    assignment = DoctorAssignment(
        assignment_id="assignment-001",
        session_id="session-001",
        doctor_id="doctor-001",
        department_id="general-medicine",
        status=AssignmentStatus.COMPLETED,
    )

    assert assignment.status == AssignmentStatus.COMPLETED


def test_assignment_can_be_released():
    timestamp = datetime.now(timezone.utc)

    assignment = DoctorAssignment(
        assignment_id="assignment-001",
        session_id="session-001",
        doctor_id="doctor-001",
        department_id="general-medicine",
        status=AssignmentStatus.RELEASED,
        released_at=timestamp,
    )

    assert assignment.status == AssignmentStatus.RELEASED
    assert assignment.released_at == timestamp
