from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.assignment import AssignmentRepository
from backend.database.repositories.doctor import DoctorRepository
from backend.domain.assignment import DoctorAssignment
from backend.domain.doctor import Doctor
from backend.domain.enums import AssignmentStatus, QueueStatus
from backend.domain.queue import QueueEntry
from backend.models.assignment import DoctorAssignmentDocument
from backend.models.doctor import DoctorDocument
from backend.services.assignment import AssignmentService
from backend.services.assignment_scheduler import AssignmentSchedulerService


@pytest.fixture
def doctor_repository() -> DoctorRepository:
    return AsyncMock(spec=DoctorRepository)


@pytest.fixture
def assignment_repository() -> AssignmentRepository:
    return AsyncMock(spec=AssignmentRepository)


@pytest.fixture
def assignment_service(assignment_repository: AssignmentRepository) -> AssignmentService:
    return AssignmentService(assignment_repository)


@pytest.fixture
def service(
    doctor_repository: DoctorRepository,
    assignment_repository: AssignmentRepository,
    assignment_service: AssignmentService,
) -> AssignmentSchedulerService:
    return AssignmentSchedulerService(
        doctor_repository,
        assignment_repository,
        assignment_service,
    )


def make_entry() -> QueueEntry:
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


def make_doctor(
    doctor_id: str,
    available: bool = True,
) -> DoctorDocument:
    timestamp = datetime.now(timezone.utc)

    return DoctorDocument(
        doctor_id=doctor_id,
        display_name=doctor_id,
        department_ids=["medicine"],
        is_available=available,
        created_at=timestamp,
        updated_at=timestamp,
    )


def make_assignment(doctor_id: str) -> DoctorAssignmentDocument:
    timestamp = datetime.now(timezone.utc)

    return DoctorAssignmentDocument(
        assignment_id=f"assignment-{doctor_id}",
        session_id=f"session-{doctor_id}",
        doctor_id=doctor_id,
        department_id="medicine",
        status=AssignmentStatus.ACTIVE,
        assigned_at=timestamp,
        released_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_select_doctor_prefers_lower_workload(
    service: AssignmentSchedulerService,
    doctor_repository: DoctorRepository,
    assignment_repository: AssignmentRepository,
) -> None:
    doctor_repository.get_department_doctors.return_value = [
        make_doctor("doctor-1"),
        make_doctor("doctor-2"),
    ]
    assignment_repository.get_doctor_assignments.side_effect = [
        [make_assignment("doctor-1")],
        [],
    ]

    result = await service.select_doctor(make_entry())

    assert result == "doctor-2"


@pytest.mark.asyncio
async def test_select_doctor_ignores_unavailable_doctors(
    service: AssignmentSchedulerService,
    doctor_repository: DoctorRepository,
    assignment_repository: AssignmentRepository,
) -> None:
    doctor_repository.get_department_doctors.return_value = [
        make_doctor("doctor-1", available=False),
        make_doctor("doctor-2"),
    ]
    assignment_repository.get_doctor_assignments.return_value = []

    result = await service.select_doctor(make_entry())

    assert result == "doctor-2"
    assignment_repository.get_doctor_assignments.assert_awaited_once_with(
        "doctor-2")


@pytest.mark.asyncio
async def test_select_doctor_returns_none_when_no_doctor_available(
    service: AssignmentSchedulerService,
    doctor_repository: DoctorRepository,
) -> None:
    doctor_repository.get_department_doctors.return_value = [
        make_doctor("doctor-1", available=False),
    ]

    result = await service.select_doctor(make_entry())

    assert result is None


@pytest.mark.asyncio
async def test_select_doctor_returns_none_when_department_has_no_doctors(
    service: AssignmentSchedulerService,
    doctor_repository: DoctorRepository,
) -> None:
    doctor_repository.get_department_doctors.return_value = []

    result = await service.select_doctor(make_entry())

    assert result is None


@pytest.mark.asyncio
async def test_assign_creates_assignment(
    service: AssignmentSchedulerService,
    doctor_repository: DoctorRepository,
    assignment_repository: AssignmentRepository,
) -> None:
    doctor_repository.get_department_doctors.return_value = [
        make_doctor("doctor-1"),
    ]
    assignment_repository.get_doctor_assignments.return_value = []

    result = await service.assign(make_entry())

    assert result is not None
    assert result.doctor_id == "doctor-1"
    assert result.session_id == "session-1"
    assert result.department_id == "medicine"
    assert result.status == AssignmentStatus.ACTIVE


@pytest.mark.asyncio
async def test_assign_returns_none_when_no_doctor_available(
    service: AssignmentSchedulerService,
    doctor_repository: DoctorRepository,
) -> None:
    doctor_repository.get_department_doctors.return_value = []

    result = await service.assign(make_entry())

    assert result is None


@pytest.mark.asyncio
async def test_assign_rejects_non_waiting_entry(
    service: AssignmentSchedulerService,
) -> None:
    entry = make_entry()
    entry.status = QueueStatus.CALLED

    with pytest.raises(ValueError, match="Queue entry must be waiting before assignment"):
        await service.assign(entry)


@pytest.mark.asyncio
async def test_assign_rejects_already_assigned_entry(
    service: AssignmentSchedulerService,
) -> None:
    entry = make_entry()
    entry.doctor_id = "doctor-1"

    with pytest.raises(ValueError, match="Queue entry is already assigned"):
        await service.assign(entry)
