from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_assignment_repository
from backend.auth.authorization import require_assigned_doctor_access
from backend.domain.enums import ActorRole, AssignmentStatus
from backend.domain.user import User
from backend.main import app


def make_user(
    actor_id: str,
) -> User:
    now = datetime.now(timezone.utc)

    return User(
        user_id=f"user-{actor_id}",
        username=actor_id,
        password_hash="",
        role=ActorRole.DOCTOR,
        actor_id=actor_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_assignment():
    now = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "session-1",
            "doctor_id": "doctor-1",
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": now,
            "released_at": None,
            "created_at": now,
            "updated_at": now,
        },
    )()


def override_access(user: User):
    app.dependency_overrides[
        require_assigned_doctor_access
    ] = lambda: user


def test_get_assignment_returns_assignment():
    repository = AsyncMock()
    repository.get_session_assignment.return_value = make_assignment()

    override_access(make_user("doctor-1"))
    app.dependency_overrides[get_assignment_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/sessions/session-1/assignment",
            )

        assert response.status_code == 200
        assert response.json()["data"]["assignment_id"] == "assignment-1"
        assert response.json()["data"]["doctor_id"] == "doctor-1"
        assert response.json()["data"]["status"] == "ACTIVE"
        repository.get_session_assignment.assert_awaited_once_with(
            "session-1",
        )
    finally:
        app.dependency_overrides.clear()


def test_get_assignment_returns_404_when_missing():
    repository = AsyncMock()
    repository.get_session_assignment.return_value = None

    override_access(make_user("doctor-1"))
    app.dependency_overrides[get_assignment_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/sessions/session-1/assignment",
            )

        assert response.status_code == 404
        repository.get_session_assignment.assert_awaited_once_with(
            "session-1",
        )
    finally:
        app.dependency_overrides.clear()


def test_get_assignment_requires_authentication():
    repository = AsyncMock()

    app.dependency_overrides[get_assignment_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/sessions/session-1/assignment",
            )

        assert response.status_code == 401
        repository.get_session_assignment.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()
