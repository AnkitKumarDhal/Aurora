from datetime import datetime, timezone

from backend.database.repositories.queue import QueueRepository
from backend.domain.enums import QueueStatus
from backend.domain.queue import QueueEntry
from backend.models.queue import QueueEntryDocument
from backend.services.queue_engine import QueueEngine


class QueueService:
    def __init__(self, repository: QueueRepository, engine: QueueEngine | None = None) -> None:
        self.repository = repository
        self.engine = engine or QueueEngine()

    async def get_department_queue(self, department_id: str,) -> list[QueueEntry]:
        documents = await self.repository.get_department_queue(department_id)
        entries = [
            self._to_domain(document)
            for document in documents
        ]
        return self.engine.sort_entries(entries)

    async def get_entry(self, queue_entry_id: str,) -> QueueEntry | None:
        document = await self.repository.get_entry(queue_entry_id)
        if document is None:
            return None
        return self._to_domain(document)

    async def get_session_entry(self, session_id: str,) -> QueueEntry | None:
        document = await self.repository.get_session_entry(session_id)
        if document is None:
            return None
        return self._to_domain(document)

    async def enqueue(self, entry: QueueEntry,) -> QueueEntry:
        if entry.status != QueueStatus.WAITING:
            raise ValueError(
                "Queue entry must be waiting when added to the queue")
        if entry.queued_at is None:
            entry.queued_at = datetime.now(timezone.utc)
        document = self._to_document(entry)
        await self.repository.create_entry(document)
        return entry

    async def update_entry(self, queue_entry_id: str, updates: dict,) -> QueueEntry | None:
        document = await self.repository.update_entry(queue_entry_id, updates,)
        if document is None:
            return None
        return self._to_domain(document)

    async def mark_called(self, queue_entry_id: str,) -> QueueEntry | None:
        return await self.update_entry(queue_entry_id, {
            "status": QueueStatus.CALLED,
            "called_at": datetime.now(timezone.utc),
        },
        )

    async def start_consultation(self, queue_entry_id: str,) -> QueueEntry | None:
        return await self.update_entry(queue_entry_id, {
            "status": QueueStatus.IN_CONSULTATION,
        },
        )

    async def complete(self, queue_entry_id: str,) -> QueueEntry | None:
        return await self.update_entry(queue_entry_id, {
            "status": QueueStatus.COMPLETED,
            "completed_at": datetime.now(timezone.utc),
        },
        )

    @staticmethod
    def _to_domain(document: QueueEntryDocument,) -> QueueEntry:
        return QueueEntry(
            queue_entry_id=document.queue_entry_id,
            session_id=document.session_id,
            department_id=document.department_id,
            status=document.status,
            position=document.position,
            urgency_level=document.urgency_level,
            priority_score=document.priority_score,
            doctor_id=document.doctor_id,
            queued_at=document.queued_at,
            called_at=document.called_at,
            completed_at=document.completed_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _to_document(entry: QueueEntry,) -> QueueEntryDocument:
        return QueueEntryDocument(
            queue_entry_id=entry.queue_entry_id,
            session_id=entry.session_id,
            department_id=entry.department_id,
            status=entry.status,
            position=entry.position,
            urgency_level=entry.urgency_level,
            priority_score=entry.priority_score,
            doctor_id=entry.doctor_id,
            queued_at=entry.queued_at,
            called_at=entry.called_at,
            completed_at=entry.completed_at,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
