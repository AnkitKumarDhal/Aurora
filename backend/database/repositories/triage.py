from backend.models.triage import TriageResultDocument
from .base import BaseRepository


class TriageRepository(BaseRepository[TriageResultDocument]):
    collection_name = TriageResultDocument.collection_name
    model = TriageResultDocument

    async def get_result(self, triage_result_id: str,) -> TriageResultDocument | None:
        return await self.get_one({"triage_result_id": triage_result_id})

    async def get_session_result(self, session_id: str,) -> TriageResultDocument | None:
        return await self.get_one({"session_id": session_id})

    async def create_result(self, result: TriageResultDocument,) -> TriageResultDocument:
        return await self.create(result)

    async def update_result(self, triage_result_id: str, updates: dict,) -> TriageResultDocument | None:
        return await self.update_one({"triage_result_id": triage_result_id}, updates,)
