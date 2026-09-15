from backend.models.clinical_summary import ClinicalSummaryDocument
from .base import BaseRepository


class ClinicalSummaryRepository(BaseRepository[ClinicalSummaryDocument]):
    collection_name = ClinicalSummaryDocument.collection_name
    model = ClinicalSummaryDocument

    async def get_summary(self, summary_id: str,) -> ClinicalSummaryDocument | None:
        return await self.get_one({"summary_id": summary_id})

    async def get_session_summary(self, session_id: str,) -> ClinicalSummaryDocument | None:
        return await self.get_one({"session_id": session_id})

    async def create_summary(self, summary: ClinicalSummaryDocument,) -> ClinicalSummaryDocument:
        return await self.create(summary)

    async def update_summary(self, summary_id: str, updates: dict,) -> ClinicalSummaryDocument | None:
        return await self.update_one({"summary_id": summary_id}, updates,)
