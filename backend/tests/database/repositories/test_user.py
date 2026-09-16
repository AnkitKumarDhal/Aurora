from unittest.mock import AsyncMock
import pytest
from backend.database.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_get_by_username_uses_base_repository():
    repository = UserRepository()
    repository.get_one = AsyncMock(
        return_value=None,
    )

    result = await repository.get_by_username(
        "doctor",
    )

    assert result is None

    repository.get_one.assert_awaited_once_with({
        "username": "doctor",
    })


@pytest.mark.asyncio
async def test_get_user_uses_base_repository():
    repository = UserRepository()
    repository.get_one = AsyncMock(
        return_value=None,
    )

    result = await repository.get_user(
        "user-1",
    )

    assert result is None

    repository.get_one.assert_awaited_once_with({
        "user_id": "user-1",
    })
