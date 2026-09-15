from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.promotion import PromotionRepository
from backend.domain.enums import PromotionStatus
from backend.domain.promotion import PromotionRequest
from backend.models.promotion import PromotionRequestDocument
from backend.services.promotion import PromotionService


@pytest.fixture
def repository() -> PromotionRepository:
    return AsyncMock(spec=PromotionRepository)


@pytest.fixture
def service(repository: PromotionRepository) -> PromotionService:
    return PromotionService(repository)


@pytest.fixture
def document() -> PromotionRequestDocument:
    timestamp = datetime.now(timezone.utc)

    return PromotionRequestDocument(
        promotion_request_id="promotion-1",
        queue_entry_id="queue-1",
        reason="Patient has been waiting beyond expected time.",
        status=PromotionStatus.PENDING,
        decision_deadline=timestamp + timedelta(seconds=60),
        decided_by=None,
        decision_reason=None,
        decided_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_request(
    service: PromotionService,
    repository: PromotionRepository,
    document: PromotionRequestDocument,
) -> None:
    repository.get_request.return_value = document

    result = await service.get_request("promotion-1")

    assert result is not None
    assert result.promotion_request_id == "promotion-1"
    assert result.queue_entry_id == "queue-1"
    assert result.status == PromotionStatus.PENDING

    repository.get_request.assert_awaited_once_with("promotion-1")


@pytest.mark.asyncio
async def test_get_request_missing(
    service: PromotionService,
    repository: PromotionRepository,
) -> None:
    repository.get_request.return_value = None

    result = await service.get_request("missing")

    assert result is None


@pytest.mark.asyncio
async def test_get_queue_request(
    service: PromotionService,
    repository: PromotionRepository,
    document: PromotionRequestDocument,
) -> None:
    repository.get_queue_request.return_value = document

    result = await service.get_queue_request("queue-1")

    assert result is not None
    assert result.queue_entry_id == "queue-1"

    repository.get_queue_request.assert_awaited_once_with("queue-1")


@pytest.mark.asyncio
async def test_get_pending_requests(
    service: PromotionService,
    repository: PromotionRepository,
    document: PromotionRequestDocument,
) -> None:
    repository.get_pending_requests.return_value = [document]

    result = await service.get_pending_requests()

    assert len(result) == 1
    assert result[0].promotion_request_id == "promotion-1"

    repository.get_pending_requests.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_request(
    service: PromotionService,
    repository: PromotionRepository,
) -> None:
    timestamp = datetime.now(timezone.utc)

    request = PromotionRequest(
        promotion_request_id="promotion-1",
        queue_entry_id="queue-1",
        reason="Patient requires review.",
        status=PromotionStatus.PENDING,
        decision_deadline=timestamp + timedelta(seconds=60),
        created_at=timestamp,
        updated_at=timestamp,
    )

    result = await service.create_request(request)

    assert result is request
    repository.create_request.assert_awaited_once()

    created_document = repository.create_request.await_args.args[0]

    assert created_document.promotion_request_id == "promotion-1"
    assert created_document.queue_entry_id == "queue-1"
    assert created_document.status == PromotionStatus.PENDING


@pytest.mark.asyncio
async def test_approve(
    service: PromotionService,
    repository: PromotionRepository,
    document: PromotionRequestDocument,
) -> None:
    approved = document.model_copy(
        update={
            "status": PromotionStatus.APPROVED,
            "decided_by": "admin-1",
            "decision_reason": "Approved by reception.",
            "decided_at": datetime.now(timezone.utc),
        },
    )

    repository.get_request.return_value = document
    repository.update_request.return_value = approved

    result = await service.approve(
        "promotion-1",
        decided_by="admin-1",
        decision_reason="Approved by reception.",
    )

    assert result is not None
    assert result.status == PromotionStatus.APPROVED
    assert result.decided_by == "admin-1"

    repository.update_request.assert_awaited_once()

    updates = repository.update_request.await_args.args[1]

    assert updates["status"] == PromotionStatus.APPROVED
    assert updates["decided_by"] == "admin-1"
    assert updates["decision_reason"] == "Approved by reception."
    assert updates["decided_at"] is not None


@pytest.mark.asyncio
async def test_deny(
    service: PromotionService,
    repository: PromotionRepository,
    document: PromotionRequestDocument,
) -> None:
    denied = document.model_copy(
        update={
            "status": PromotionStatus.DENIED,
            "decided_by": "admin-1",
            "decision_reason": "Insufficient justification.",
            "decided_at": datetime.now(timezone.utc),
        },
    )

    repository.get_request.return_value = document
    repository.update_request.return_value = denied

    result = await service.deny(
        "promotion-1",
        decided_by="admin-1",
        decision_reason="Insufficient justification.",
    )

    assert result is not None
    assert result.status == PromotionStatus.DENIED
    assert result.decided_by == "admin-1"


@pytest.mark.asyncio
async def test_expire(
    service: PromotionService,
    repository: PromotionRepository,
    document: PromotionRequestDocument,
) -> None:
    expired = document.model_copy(
        update={
            "status": PromotionStatus.EXPIRED,
            "decision_reason": "Promotion decision window expired.",
            "decided_at": datetime.now(timezone.utc),
        },
    )

    repository.get_request.return_value = document
    repository.update_request.return_value = expired

    result = await service.expire("promotion-1")

    assert result is not None
    assert result.status == PromotionStatus.EXPIRED

    repository.update_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_expired_request_cannot_be_approved(
    service: PromotionService,
    repository: PromotionRepository,
) -> None:
    timestamp = datetime.now(timezone.utc)

    document = PromotionRequestDocument(
        promotion_request_id="promotion-1",
        queue_entry_id="queue-1",
        reason="Patient requires review.",
        status=PromotionStatus.PENDING,
        decision_deadline=timestamp - timedelta(seconds=1),
        created_at=timestamp,
        updated_at=timestamp,
    )

    expired = document.model_copy(
        update={
            "status": PromotionStatus.EXPIRED,
            "decision_reason": "Promotion decision window expired.",
            "decided_at": datetime.now(timezone.utc),
        },
    )

    repository.get_request.return_value = document
    repository.update_request.return_value = expired

    result = await service.approve("promotion-1", decided_by="admin-1")

    assert result is not None
    assert result.status == PromotionStatus.EXPIRED

    repository.update_request.assert_awaited_once()

    updates = repository.update_request.await_args.args[1]

    assert updates["status"] == PromotionStatus.EXPIRED


@pytest.mark.asyncio
async def test_already_decided_request_is_unchanged(
    service: PromotionService,
    repository: PromotionRepository,
) -> None:
    timestamp = datetime.now(timezone.utc)

    document = PromotionRequestDocument(
        promotion_request_id="promotion-1",
        queue_entry_id="queue-1",
        reason="Patient requires review.",
        status=PromotionStatus.DENIED,
        decision_deadline=timestamp + timedelta(seconds=60),
        decided_by="admin-1",
        decision_reason="Denied.",
        decided_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )

    repository.get_request.return_value = document

    result = await service.approve("promotion-1", decided_by="admin-2")

    assert result is not None
    assert result.status == PromotionStatus.DENIED
    assert result.decided_by == "admin-1"

    repository.update_request.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel(
    service: PromotionService,
    repository: PromotionRepository,
    document: PromotionRequestDocument,
) -> None:
    cancelled = document.model_copy(
        update={
            "status": PromotionStatus.CANCELLED,
            "decision_reason": "Promotion no longer required.",
            "decided_at": datetime.now(timezone.utc),
        },
    )

    repository.get_request.return_value = document
    repository.update_request.return_value = cancelled

    result = await service.cancel(
        "promotion-1",
        "Promotion no longer required.",
    )

    assert result is not None
    assert result.status == PromotionStatus.CANCELLED
    assert result.decision_reason == "Promotion no longer required."


@pytest.mark.asyncio
async def test_expire_pending_requests(
    service: PromotionService,
    repository: PromotionRepository,
) -> None:
    now = datetime.now(timezone.utc)

    expired_document = PromotionRequestDocument(
        promotion_request_id="promotion-1",
        queue_entry_id="queue-1",
        reason="Expired request.",
        status=PromotionStatus.PENDING,
        decision_deadline=now - timedelta(seconds=1),
        created_at=now,
        updated_at=now,
    )

    active_document = PromotionRequestDocument(
        promotion_request_id="promotion-2",
        queue_entry_id="queue-2",
        reason="Active request.",
        status=PromotionStatus.PENDING,
        decision_deadline=now + timedelta(seconds=60),
        created_at=now,
        updated_at=now,
    )

    expired_result = expired_document.model_copy(
        update={
            "status": PromotionStatus.EXPIRED,
            "decision_reason": "Promotion decision window expired.",
            "decided_at": datetime.now(timezone.utc),
        },
    )

    repository.get_pending_requests.return_value = [
        expired_document,
        active_document,
    ]
    repository.get_request.return_value = expired_document
    repository.update_request.return_value = expired_result

    result = await service.expire_pending_requests()

    assert len(result) == 1
    assert result[0].promotion_request_id == "promotion-1"
    assert result[0].status == PromotionStatus.EXPIRED
