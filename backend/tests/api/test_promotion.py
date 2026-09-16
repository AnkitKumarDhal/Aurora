from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_promotion_service
from backend.domain.enums import PromotionStatus
from backend.domain.promotion import PromotionRequest
from backend.main import app


def make_request(
    status: PromotionStatus = PromotionStatus.PENDING,
) -> PromotionRequest:
    timestamp = datetime.now(timezone.utc)

    return PromotionRequest(
        promotion_request_id="promotion-1",
        queue_entry_id="queue-1",
        reason="Earlier available doctor",
        status=status,
        decision_deadline=timestamp + timedelta(seconds=60),
        decided_by=None,
        decision_reason=None,
        decided_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def make_service() -> AsyncMock:
    return AsyncMock()


def override_service(service: AsyncMock):
    app.dependency_overrides[
        get_promotion_service
    ] = lambda: service


def clear_override():
    app.dependency_overrides.pop(
        get_promotion_service,
        None,
    )


def test_get_promotion():
    service = make_service()
    service.get_request.return_value = make_request()

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/promotions/promotion-1"
            )

        assert response.status_code == 200
        assert (
            response.json()["data"]["promotion_request_id"]
            == "promotion-1"
        )
    finally:
        clear_override()


def test_get_promotion_not_found():
    service = make_service()
    service.get_request.return_value = None

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/promotions/missing"
            )

        assert response.status_code == 404
    finally:
        clear_override()


def test_create_promotion():
    service = make_service()
    service.create_promotion_request.return_value = (
        make_request()
    )

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/promotions",
                json={
                    "queue_entry_id": "queue-1",
                    "reason": "Earlier available doctor",
                },
            )

        assert response.status_code == 200
        assert (
            response.json()["data"]["status"]
            == "PENDING"
        )
    finally:
        clear_override()


def test_approve_promotion():
    service = make_service()
    service.approve.return_value = make_request(
        PromotionStatus.APPROVED
    )

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/promotions/promotion-1/approve",
                json={
                    "decision_reason": "Approved",
                },
            )

        assert response.status_code == 200
        assert (
            response.json()["data"]["status"]
            == "APPROVED"
        )
    finally:
        clear_override()


def test_deny_promotion():
    service = make_service()
    service.deny.return_value = make_request(
        PromotionStatus.DENIED
    )

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/promotions/promotion-1/deny",
                json={
                    "decision_reason": "Keep current assignment",
                },
            )

        assert response.status_code == 200
        assert (
            response.json()["data"]["status"]
            == "DENIED"
        )
    finally:
        clear_override()
