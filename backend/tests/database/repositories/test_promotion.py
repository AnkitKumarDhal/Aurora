# backend/tests/database/repositories/test_promotion.py

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.database.repositories.promotion import PromotionRepository
from backend.domain.enums import PromotionStatus


@pytest.mark.asyncio
async def test_get_pending_requests_uses_lazy_collection():
    repository = PromotionRepository()

    collection = MagicMock()
    cursor = AsyncMock()
    cursor.__aiter__.return_value = iter([])
    collection.find.return_value = cursor

    repository._get_collection = MagicMock(
        return_value=collection
    )

    result = await repository.get_pending_requests()

    assert result == []

    repository._get_collection.assert_called_once_with()

    collection.find.assert_called_once_with(
        {"status": PromotionStatus.PENDING},
        sort=[("decision_deadline", 1)],
    )
