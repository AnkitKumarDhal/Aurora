from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_promotion_service
from backend.auth.dependencies import get_current_user
from backend.domain.enums import ActorRole, PromotionStatus
from backend.domain.promotion import PromotionRequest
from backend.domain.user import User
from backend.main import app


def make_request(status: PromotionStatus = PromotionStatus.PENDING) -> PromotionRequest:
    return PromotionRequest(
        promotion_request_id="promotion-1",
        queue_entry_id="queue-1",
        reason="Urgent patient",
        status=status,
        decision_deadline=datetime.now(timezone.utc) + timedelta(seconds=60),
    )


def make_service() -> MagicMock:
    service = MagicMock()
    service.get_pending_requests = AsyncMock(return_value=[])
    service.get_request = AsyncMock(return_value=make_request())
    service.create_promotion_request = AsyncMock(return_value=make_request())
    service.approve = AsyncMock(
        return_value=make_request(PromotionStatus.APPROVED))
    service.deny = AsyncMock(return_value=make_request(PromotionStatus.DENIED))
    service.cancel = AsyncMock(
        return_value=make_request(PromotionStatus.CANCELLED))
    return service


def make_admin_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        user_id="user-admin-1",
        username="admin",
        password_hash="",
        role=ActorRole.ADMIN,
        actor_id="admin-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def override_service(service: MagicMock) -> None:
    app.dependency_overrides[get_promotion_service] = lambda: service


def override_admin_user() -> None:
    app.dependency_overrides[get_current_user] = make_admin_user


def clear_overrides() -> None:
    app.dependency_overrides.pop(get_promotion_service, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_get_pending_promotions():
    service = make_service()
    service.get_pending_requests.return_value = [make_request()]
    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/promotions/pending")

        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
        service.get_pending_requests.assert_awaited_once()
    finally:
        clear_overrides()


def test_get_promotion():
    service = make_service()
    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/promotions/promotion-1")

        assert response.status_code == 200
        assert response.json()["data"]["promotion_request_id"] == "promotion-1"
        service.get_request.assert_awaited_once_with("promotion-1")
    finally:
        clear_overrides()


def test_create_promotion():
    service = make_service()
    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/promotions",
                json={
                    "queue_entry_id": "queue-1",
                    "reason": "Urgent patient",
                },
            )

        assert response.status_code == 200
        assert response.json()["data"]["promotion_request_id"] == "promotion-1"
        service.create_promotion_request.assert_awaited_once_with(
            "queue-1",
            "Urgent patient",
        )
    finally:
        clear_overrides()


def test_approve_promotion():
    service = make_service()
    override_service(service)
    override_admin_user()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/promotions/promotion-1/approve",
                json={
                    "decision_reason": "Approved",
                },
            )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "APPROVED"
        service.approve.assert_awaited_once_with(
            "promotion-1",
            decided_by="admin-1",
            decision_reason="Approved",
        )
    finally:
        clear_overrides()


def test_deny_promotion():
    service = make_service()
    override_service(service)
    override_admin_user()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/promotions/promotion-1/deny",
                json={
                    "decision_reason": "Keep current assignment",
                },
            )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "DENIED"
        service.deny.assert_awaited_once_with(
            "promotion-1",
            decided_by="admin-1",
            decision_reason="Keep current assignment",
        )
    finally:
        clear_overrides()
