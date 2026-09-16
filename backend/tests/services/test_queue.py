from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from backend.domain.enums import QueueStatus, UrgencyLevel
from backend.models.queue import QueueEntryDocument
from backend.services.queue import QueueService


def make_document(
    queue_entry_id: str,
    priority_score: int,
    queued_at: datetime,
) -> QueueEntryDocument:
    timestamp = datetime.now(timezone.utc)

    return QueueEntryDocument(
        queue_entry_id=queue_entry_id,
        session_id=f"session-{queue_entry_id}",
        department_id="general-medicine",
        status=QueueStatus.WAITING,
        position=None,
        urgency_level=UrgencyLevel.LEVEL_1,
        priority_score=priority_score,
        doctor_id=None,
        queued_at=queued_at,
        called_at=None,
        completed_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_department_queue_uses_queue_engine():
    repository = AsyncMock()
    now = datetime.now(timezone.utc)

    repository.get_department_queue.return_value = [
        make_document("newer-high", 50, now),
        make_document("older-low", 45, now - timedelta(minutes=20)),
    ]

    service = QueueService(repository)

    entries = await service.get_department_queue("general-medicine")

    assert [entry.queue_entry_id for entry in entries] == [
        "older-low",
        "newer-high",
    ]


@pytest.mark.asyncio
async def test_get_department_queue_returns_only_waiting_entries():
    repository = AsyncMock()
    now = datetime.now(timezone.utc)

    repository.get_department_queue.return_value = [
        make_document("patient-1", 80, now),
        make_document("patient-2", 40, now),
    ]

    service = QueueService(repository)

    entries = await service.get_department_queue("general-medicine")

    assert all(entry.status == QueueStatus.WAITING for entry in entries)
    repository.get_department_queue.assert_awaited_once_with(
        "general-medicine"
    )
