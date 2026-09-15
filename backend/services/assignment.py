from datetime import datetime, timezone

from backend.database.repositories.assignment import AssignmentRepository
from backend.domain.assignment import DoctorAssignment
from backend.domain.enums import AssignmentStatus
from backend.models.assignment import DoctorAssignmentDocument


class AssignmentService:
    def __init__(self, repository: AssignmentRepository,) -> None:
        self.repository = repository

    async def get_session_assignment(self, session_id: str,) -> DoctorAssignment | None:
        document = await self.repository.get_session_assignment(session_id)
        if document is None:
            return None
        return self._to_domain(document)

    async def get_doctor_assignments(self, doctor_id: str,) -> list[DoctorAssignment]:
        documents = await self.repository.get_doctor_assignments(doctor_id)
        return [
            self._to_domain(document)
            for document in documents
        ]

    async def create_assignment(self, assignment: DoctorAssignment,) -> DoctorAssignment:
        if assignment.assigned_at is None:
            assignment.assigned_at = datetime.now(timezone.utc)
        document = self._to_document(assignment)
        await self.repository.create_assignment(document)
        return assignment

    async def release_assignment(self, assignment_id: str,) -> DoctorAssignment | None:
        document = await self.repository.update_assignment(assignment_id, {
            "status": AssignmentStatus.RELEASED,
            "released_at": datetime.now(timezone.utc),
        },
        )

        if document is None:
            return None
        return self._to_domain(document)

    async def complete_assignment(self, assignment_id: str,) -> DoctorAssignment | None:
        document = await self.repository.update_assignment(assignment_id, {
            "status": AssignmentStatus.COMPLETED,
        },
        )

        if document is None:
            return None
        return self._to_domain(document)

    @staticmethod
    def _to_domain(document: DoctorAssignmentDocument,) -> DoctorAssignment:
        return DoctorAssignment(
            assignment_id=document.assignment_id,
            session_id=document.session_id,
            doctor_id=document.doctor_id,
            department_id=document.department_id,
            status=document.status,
            assigned_at=document.assigned_at,
            released_at=document.released_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _to_document(assignment: DoctorAssignment,) -> DoctorAssignmentDocument:
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
