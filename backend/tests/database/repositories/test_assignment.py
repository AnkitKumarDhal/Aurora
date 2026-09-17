from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.database.repositories.assignment import AssignmentRepository
from backend.domain.enums import AssignmentStatus


@pytest.mark.asyncio
async def test_get_doctor_assignments_uses_lazy_collection():
    repository = AssignmentRepository()

    collection = MagicMock()
    cursor = AsyncMock()
    cursor.__aiter__.return_value = iter([])
    collection.find.return_value = cursor

    repository._get_collection = MagicMock(return_value=collection)

    result = await repository.get_doctor_assignments("doctor-1")

    assert result == []

    repository._get_collection.assert_called_once_with()

    collection.find.assert_called_once_with(
        {
            "doctor_id": "doctor-1",
            "status": AssignmentStatus.ACTIVE,
        },
    )


@pytest.mark.asyncio
async def test_get_session_assignment_history_reads_any_assignment_status():
    repository = AssignmentRepository()

    timestamp = datetime.now(timezone.utc)

    collection = MagicMock()
    document = {
        "assignment_id": "assignment-1",
        "session_id": "session-1",
        "doctor_id": "doctor-1",
        "department_id": "general-medicine",
        "status": AssignmentStatus.RELEASED,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    collection.find_one = AsyncMock(return_value=document)
    repository._get_collection = MagicMock(return_value=collection)

    result = await repository.get_session_assignment_history(
        "session-1",
    )

    assert result is not None
    assert result.assignment_id == "assignment-1"
    assert result.status == AssignmentStatus.RELEASED

    repository._get_collection.assert_called_once_with()
    collection.find_one.assert_awaited_once_with(
        {
            "session_id": "session-1",
        },
    )
