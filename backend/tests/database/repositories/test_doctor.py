from unittest.mock import AsyncMock, MagicMock
import pytest
from backend.database.repositories.doctor import DoctorRepository


@pytest.mark.asyncio
async def test_get_department_doctors_uses_lazy_collection():
    repository = DoctorRepository()

    collection = MagicMock()
    cursor = AsyncMock()
    cursor.__aiter__.return_value = iter([])
    collection.find.return_value = cursor

    repository._get_collection = MagicMock(return_value=collection)

    result = await repository.get_department_doctors(
        "general-medicine"
    )

    assert result == []

    repository._get_collection.assert_called_once_with()

    collection.find.assert_called_once_with({
        "department_ids": "general-medicine",
    })


@pytest.mark.asyncio
async def test_get_available_department_doctors_uses_lazy_collection():
    repository = DoctorRepository()

    collection = MagicMock()
    cursor = AsyncMock()
    cursor.__aiter__.return_value = iter([])
    collection.find.return_value = cursor

    repository._get_collection = MagicMock(return_value=collection)

    result = await repository.get_available_department_doctors(
        "general-medicine"
    )

    assert result == []

    repository._get_collection.assert_called_once_with()

    collection.find.assert_called_once_with({
        "department_ids": "general-medicine",
        "is_available": True,
    })
