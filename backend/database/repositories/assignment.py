from backend.models.assignment import DoctorAssignmentDocument
from .base import BaseRepository


class AssignmentRepository(BaseRepository[DoctorAssignmentDocument]):
    collection_name = DoctorAssignmentDocument.collection_name
    model = DoctorAssignmentDocument

    async def get_assignment(self, assignment_id: str,) -> DoctorAssignmentDocument | None:
        return await self.get_one({"assignment_id": assignment_id})

    async def get_session_assignment(self, session_id: str,) -> DoctorAssignmentDocument | None:
        return await self.get_one({
            "session_id": session_id,
            "status": "active",
        })

    async def get_doctor_assignments(self, doctor_id: str,) -> list[DoctorAssignmentDocument]:
        cursor = self.collection.find({
            "doctor_id": doctor_id,
            "status": "active",
        })

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_assignment(self, assignment: DoctorAssignmentDocument,) -> DoctorAssignmentDocument:
        return await self.create(assignment)

    async def update_assignment(self, assignment_id: str, updates: dict,) -> DoctorAssignmentDocument | None:
        return await self.update_one({"assignment_id": assignment_id}, updates,)
