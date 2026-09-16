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

    collection.find.assert_called_once_with({
        "doctor_id": "doctor-1",
        "status": AssignmentStatus.ACTIVE,
    })
