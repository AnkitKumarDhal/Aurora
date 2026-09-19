from backend.models.clinical_signal import ClinicalSignalDocument

from .base import BaseRepository


class ClinicalSignalRepository(BaseRepository[ClinicalSignalDocument]):
    collection_name = ClinicalSignalDocument.collection_name
    model = ClinicalSignalDocument

    async def get_signal(
        self,
        signal_id: str,
    ) -> ClinicalSignalDocument | None:
        return await self.get_one(
            {"signal_id": signal_id},
        )

    async def get_session_signals(
        self,
        session_id: str,
    ) -> list[ClinicalSignalDocument]:
        collection = self._get_collection()

        cursor = collection.find(
            {"session_id": session_id},
            sort=[("created_at", 1)],
        )

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_signal(
        self,
        signal: ClinicalSignalDocument,
    ) -> ClinicalSignalDocument:
        return await self.create(signal)

    async def update_signal(
        self,
        signal_id: str,
        updates: dict,
    ) -> ClinicalSignalDocument | None:
        return await self.update_one(
            {"signal_id": signal_id},
            updates,
        )
