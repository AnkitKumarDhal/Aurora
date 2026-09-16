from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import pytest
from backend.database.repositories.queue import QueueRepository
from backend.domain.enums import QueueStatus, UrgencyLevel
from backend.models.queue import QueueEntryDocument


def make_document():
    timestamp = datetime.now(timezone.utc)

    return QueueEntryDocument(
        queue_entry_id="queue-1",
        session_id="session-1",
        department_id="general-medicine",
        status=QueueStatus.WAITING,
        position=1,
        urgency_level=UrgencyLevel.LEVEL_3,
        priority_score=60,
        doctor_id=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_department_queue_uses_lazy_collection():
    repository = QueueRepository()

    document = make_document()

    cursor = AsyncMock()
    cursor.__aiter__.return_value = iter(
        [document.to_mongo()]
    )

    collection = MagicMock()
    collection.find.return_value = cursor

    repository._get_collection = MagicMock(
        return_value=collection
    )

    result = await repository.get_department_queue(
        "general-medicine"
    )

    repository._get_collection.assert_called_once_with()

    collection.find.assert_called_once_with({
        "department_id": "general-medicine",
        "status": QueueStatus.WAITING,
    })

    assert len(result) == 1
    assert result[0].queue_entry_id == "queue-1"
