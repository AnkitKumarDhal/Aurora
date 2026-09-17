from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_doctor_case_service
from backend.auth.authorization import require_doctor_case_access
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.main import app


def make_user(
    role: ActorRole,
    actor_id: str,
) -> User:
    now = datetime.now(timezone.utc)

    return User(
        user_id=f"user-{actor_id}",
        username=actor_id,
        password_hash="",
        role=role,
        actor_id=actor_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def override_service(service):
    app.dependency_overrides[get_doctor_case_service] = lambda: service


def override_doctor_access(user: User):
    app.dependency_overrides[require_doctor_case_access] = lambda: user


def test_get_doctor_case_requires_authentication():
    service = AsyncMock()

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/doctors/me/cases/session-1",
            )

        assert response.status_code == 401
        service.get_case.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_get_doctor_case_uses_authenticated_doctor():
    service = AsyncMock()
    service.get_case.return_value = None

    doctor = make_user(
        ActorRole.DOCTOR,
        "doctor-1",
    )

    override_service(service)
    override_doctor_access(doctor)

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/doctors/me/cases/session-1",
            )

        assert response.status_code == 404
        service.get_case.assert_awaited_once_with("session-1")
    finally:
        app.dependency_overrides.clear()
