from .base import BaseRepository
from models.clinical_session import ClinicalSessionDocument


class ClinicalSessionRepository(BaseRepository[ClinicalSessionDocument]):
    collection_name = ClinicalSessionDocument.collection_name
    model = ClinicalSessionDocument

    async def get_session(self, session_id: str,) -> ClinicalSessionDocument | None:
        return await self.get_one({"session_id": session_id})

    async def get_patient_sessions(self, patient_id: str,) -> list[ClinicalSessionDocument]:
        cursor = self.collection.find(
            {"patient_id": patient_id}, sort=[("created_at", -1)],)
        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def get_department_sessions(self, department_id: str,) -> list[ClinicalSessionDocument]:
        cursor = self.collection.find(
            {"department_id": department_id}, sort=[("created_at", -1)],)

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_session(self, session: ClinicalSessionDocument,) -> ClinicalSessionDocument:
        return await self.create(session)

    async def update_session(self, session_id: str, updates: dict,) -> ClinicalSessionDocument | None:
        return await self.update_one({"session_id": session_id}, updates,)
