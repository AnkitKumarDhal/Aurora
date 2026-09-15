from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from database.repositories.queue import QueueRepository
from domain.enums import QueueStatus, UrgencyLevel
from models.queue import QueueEntryDocument


@pytest.fixture
def queue_entry() -> QueueEntryDocument:
    now = datetime.now(timezone.utc)

    return QueueEntryDocument(
        queue_entry_id="queue-001",
        session_id="session-001",
        department_id="general-medicine",
        status=QueueStatus.WAITING,
        position=1,
        urgency_level=UrgencyLevel.LEVEL_2,
        priority_score=75,
        doctor_id=None,
        queued_at=now,
        called_at=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def repository() -> QueueRepository:
    repository = QueueRepository()
    repository.collection = AsyncMock()
    return repository


@pytest.mark.asyncio
async def test_get_entry(repository: QueueRepository, queue_entry: QueueEntryDocument,) -> None:
    repository.collection.find_one.return_value = queue_entry.to_mongo()
    result = await repository.get_entry("queue-001")
    assert result is not None
    assert result.queue_entry_id == "queue-001"
    repository.collection.find_one.assert_awaited_once_with(
        {"queue_entry_id": "queue-001"},)


@pytest.mark.asyncio
async def test_get_session_entry(repository: QueueRepository, queue_entry: QueueEntryDocument,) -> None:
    repository.collection.find_one.return_value = queue_entry.to_mongo()
    result = await repository.get_session_entry("session-001")
    assert result is not None
    assert result.session_id == "session-001"
    repository.collection.find_one.assert_awaited_once_with(
        {"session_id": "session-001"},)
