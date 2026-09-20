from datetime import datetime

from backend.domain.enums import QueueStatus
from backend.models.queue import QueueEntryDocument

from .base import BaseRepository


class QueueRepository(BaseRepository[QueueEntryDocument]):
    collection_name = QueueEntryDocument.collection_name
    model = QueueEntryDocument

    async def get_entry(
        self,
        queue_entry_id: str,
    ) -> QueueEntryDocument | None:
        return await self.get_one(
            {
                "queue_entry_id": queue_entry_id,
            },
        )

    async def get_session_entry(
        self,
        session_id: str,
    ) -> QueueEntryDocument | None:
        return await self.get_one(
            {
                "session_id": session_id,
            },
        )

    async def get_department_queue(
        self,
        department_id: str,
    ) -> list[QueueEntryDocument]:
        collection = self._get_collection()

        cursor = collection.find(
            {
                "department_id": department_id,
                "status": QueueStatus.WAITING,
            },
        )

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def get_department_entries(
        self,
        department_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[QueueEntryDocument]:
        collection = self._get_collection()

        query: dict[str, object] = {
            "department_id": department_id,
        }

        if start_at is not None or end_at is not None:
            range_query: dict[str, datetime] = {}

            if start_at is not None:
                range_query["$gte"] = start_at

            if end_at is not None:
                range_query["$lt"] = end_at

            query["$or"] = [
                {"created_at": range_query},
                {"queued_at": range_query},
                {"called_at": range_query},
                {"completed_at": range_query},
                {"updated_at": range_query},
            ]

        cursor = collection.find(
            query,
        )

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_entry(
        self,
        entry: QueueEntryDocument,
    ) -> QueueEntryDocument:
        return await self.create(entry)

    async def update_entry(
        self,
        queue_entry_id: str,
        updates: dict,
    ) -> QueueEntryDocument | None:
        return await self.update_one(
            {
                "queue_entry_id": queue_entry_id,
            },
            updates,
        )
