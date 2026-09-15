from dataclasses import dataclass
from datetime import datetime, timezone

from backend.database.repositories.assignment import AssignmentRepository
from backend.database.repositories.doctor import DoctorRepository
from backend.domain.assignment import DoctorAssignment
from backend.domain.enums import AssignmentStatus, QueueStatus
from backend.domain.queue import QueueEntry
from backend.services.assignment import AssignmentService


@dataclass(frozen=True)
class DoctorCandidate:
    doctor_id: str
    workload: int


class AssignmentSchedulerService:
    def __init__(
        self,
        doctor_repository: DoctorRepository,
        assignment_repository: AssignmentRepository,
        assignment_service: AssignmentService,
    ) -> None:
        self.doctor_repository = doctor_repository
        self.assignment_repository = assignment_repository
        self.assignment_service = assignment_service

    async def select_doctor(self, entry: QueueEntry) -> str | None:
        doctors = await self.doctor_repository.get_department_doctors(entry.department_id)
        candidates: list[DoctorCandidate] = []
        for doctor in doctors:
            if not doctor.is_available:
                continue
            assignments = await self.assignment_repository.get_doctor_assignments(doctor.doctor_id)
            candidates.append(DoctorCandidate(
                doctor_id=doctor.doctor_id, workload=len(assignments),))
        if not candidates:
            return None
        candidates.sort(key=lambda candidate: (
            candidate.workload, candidate.doctor_id))
        return candidates[0].doctor_id

    async def assign(self, entry: QueueEntry) -> DoctorAssignment | None:
        if entry.status != QueueStatus.WAITING:
            raise ValueError("Queue entry must be waiting before assignment")
        if entry.doctor_id is not None:
            raise ValueError("Queue entry is already assigned")
        doctor_id = await self.select_doctor(entry)
        if doctor_id is None:
            return None
        timestamp = datetime.now(timezone.utc)
        assignment = DoctorAssignment(
            assignment_id=f"assignment-{entry.queue_entry_id}",
            session_id=entry.session_id,
            doctor_id=doctor_id,
            department_id=entry.department_id,
            status=AssignmentStatus.ACTIVE,
            assigned_at=timestamp,
            released_at=None,
            created_at=timestamp,
            updated_at=timestamp,
        )
        await self.assignment_service.create_assignment(assignment)
        return assignment
