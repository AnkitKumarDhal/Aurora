from backend.domain.enums import QueueStatus, SessionStatus
from backend.domain.queue import QueueEntry
from backend.services.clinical_session import ClinicalSessionService
from backend.services.queue import QueueService


class WorkflowService:
    def __init__(self, session_service: ClinicalSessionService, queue_service: QueueService,) -> None:
        self.session_service = session_service
        self.queue_service = queue_service

    async def queue_session(self, entry: QueueEntry) -> QueueEntry:
        session = await self.session_service.get_session(entry.session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.SUMMARY_READY:
            raise ValueError(
                "Session must have a ready summary before queuing")

        if entry.status != QueueStatus.WAITING:
            raise ValueError("Queue entry must be waiting")

        queued_entry = await self.queue_service.enqueue(entry)

        await self.session_service.transition_session(
            entry.session_id,
            SessionStatus.QUEUED,
        )

        return queued_entry

    async def call_patient(self, session_id: str, queue_entry_id: str) -> QueueEntry:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.ASSIGNED:
            raise ValueError(
                "Session must be assigned before calling the patient")

        entry = await self.queue_service.mark_called(queue_entry_id)

        if entry is None:
            raise ValueError("Queue entry not found")

        await self.session_service.transition_session(
            session_id,
            SessionStatus.CALLED,
        )

        return entry

    async def start_consultation(self, session_id: str, queue_entry_id: str) -> QueueEntry:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.CALLED:
            raise ValueError("Session must be called before consultation")

        entry = await self.queue_service.start_consultation(queue_entry_id)

        if entry is None:
            raise ValueError("Queue entry not found")

        await self.session_service.transition_session(
            session_id,
            SessionStatus.IN_CONSULTATION,
        )

        return entry

    async def complete_consultation(self, session_id: str, queue_entry_id: str) -> QueueEntry:
        session = await self.session_service.get_session(session_id)

        if session is None:
            raise ValueError("Clinical session not found")

        if session.status != SessionStatus.IN_CONSULTATION:
            raise ValueError("Session is not in consultation")

        entry = await self.queue_service.complete(queue_entry_id)

        if entry is None:
            raise ValueError("Queue entry not found")

        await self.session_service.transition_session(
            session_id,
            SessionStatus.COMPLETED,
        )

        return entry
