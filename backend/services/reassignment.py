from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from backend.database.repositories.assignment import (
    AssignmentRepository,
)
from backend.database.repositories.doctor import (
    DoctorRepository,
)
from backend.database.repositories.queue import (
    QueueRepository,
)
from backend.domain.enums import (
    AssignmentStatus,
    QueueStatus,
)
from backend.domain.assignment import (
    DoctorAssignment,
)
from backend.services.assignment import (
    AssignmentService,
)
from backend.services.queue import (
    QueueService,
)


REASSIGNABLE_STATUSES = {
    QueueStatus.WAITING,
    QueueStatus.READY,
    QueueStatus.CALLED,
    QueueStatus.PROMOTION_PENDING,
}


@dataclass(frozen=True)
class ReassignmentResult:
    queue_entry_id: str
    session_id: str
    previous_doctor_id: str | None
    doctor_id: str
    assignment_id: str


class ReassignmentService:
    def __init__(
        self,
        queue_repository: QueueRepository,
        assignment_repository: AssignmentRepository,
        doctor_repository: DoctorRepository,
    ) -> None:
        self.queue_repository = queue_repository
        self.assignment_repository = (
            assignment_repository
        )
        self.doctor_repository = doctor_repository

        self.queue_service = QueueService(
            queue_repository,
        )

        self.assignment_service = AssignmentService(
            assignment_repository,
        )

    async def reassign(
        self,
        queue_entry_id: str,
        doctor_id: str,
    ) -> ReassignmentResult:
        entry = await self.queue_service.get_entry(
            queue_entry_id,
        )

        if entry is None:
            raise ValueError(
                "Queue entry not found",
            )

        if entry.status not in REASSIGNABLE_STATUSES:
            raise ValueError(
                "This patient cannot be reassigned in its current state",
            )

        target_doctor = (
            await self.doctor_repository.get_doctor(
                doctor_id,
            )
        )

        if target_doctor is None:
            raise ValueError(
                "Target doctor not found",
            )

        if (
            entry.department_id
            not in target_doctor.department_ids
        ):
            raise ValueError(
                "Target doctor does not belong to this department",
            )

        if not target_doctor.is_available:
            raise ValueError(
                "Target doctor is unavailable",
            )

        active_assignment = (
            await self.assignment_service.get_session_assignment(
                entry.session_id,
            )
        )

        previous_doctor_id = (
            active_assignment.doctor_id
            if active_assignment is not None
            else entry.doctor_id
        )

        if (
            previous_doctor_id is not None
            and previous_doctor_id == doctor_id
        ):
            raise ValueError(
                "Patient is already assigned to this doctor",
            )

        if (
            active_assignment is None
            and entry.doctor_id is not None
        ):
            raise ValueError(
                "Patient assignment state is inconsistent",
            )

        released_assignment = None

        if active_assignment is not None:
            released_assignment = (
                await self.assignment_service.release_assignment(
                    active_assignment.assignment_id,
                )
            )

            if released_assignment is None:
                raise ValueError(
                    "Current doctor assignment could not be released",
                )

        timestamp = datetime.now(
            timezone.utc,
        )

        new_assignment = None

        try:
            new_assignment = (
                await self.assignment_service.create_assignment(
                    self._build_assignment(
                        queue_entry_id=queue_entry_id,
                        session_id=entry.session_id,
                        department_id=entry.department_id,
                        doctor_id=doctor_id,
                        timestamp=timestamp,
                    ),
                )
            )

            updated_entry = (
                await self.queue_service.update_entry(
                    queue_entry_id,
                    {
                        "doctor_id": doctor_id,
                        "updated_at": timestamp,
                    },
                )
            )

            if updated_entry is None:
                raise ValueError(
                    "Queue entry could not be updated",
                )

        except Exception:
            if new_assignment is not None:
                await self.assignment_service.release_assignment(
                    new_assignment.assignment_id,
                )

            if released_assignment is not None:
                await self.assignment_repository.update_assignment(
                    released_assignment.assignment_id,
                    {
                        "status": AssignmentStatus.ACTIVE,
                        "released_at": None,
                        "updated_at": datetime.now(
                            timezone.utc,
                        ),
                    },
                )

            await self.queue_service.update_entry(
                queue_entry_id,
                {
                    "doctor_id": previous_doctor_id,
                    "updated_at": datetime.now(
                        timezone.utc,
                    ),
                },
            )

            raise

        return ReassignmentResult(
            queue_entry_id=queue_entry_id,
            session_id=entry.session_id,
            previous_doctor_id=previous_doctor_id,
            doctor_id=doctor_id,
            assignment_id=new_assignment.assignment_id,
        )

    @staticmethod
    def _build_assignment(
        queue_entry_id: str,
        session_id: str,
        department_id: str,
        doctor_id: str,
        timestamp: datetime,
    ) -> DoctorAssignment:
        return DoctorAssignment(
            assignment_id=(
                f"assignment-reassign-"
                f"{queue_entry_id}-"
                f"{uuid4().hex}"
            ),
            session_id=session_id,
            doctor_id=doctor_id,
            department_id=department_id,
            status=AssignmentStatus.ACTIVE,
            assigned_at=timestamp,
            released_at=None,
            created_at=timestamp,
            updated_at=timestamp,
        )
