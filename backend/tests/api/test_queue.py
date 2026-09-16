from datetime import datetime, timezone
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from backend.api.dependencies import get_doctor_repository, get_queue_service
from backend.auth.dependencies import get_current_user
from backend.domain.enums import ActorRole, QueueStatus, UrgencyLevel
from backend.domain.user import User
from backend.main import app


def make_entry(queue_entry_id: str = "queue-1"):
    timestamp = datetime.now(timezone.utc)

    return type(
        "QueueEntry",
        (),
        {
            "queue_entry_id": queue_entry_id,
            "session_id": "session-1",
            "department_id": "general-medicine",
            "status": QueueStatus.WAITING,
            "position": 1,
            "urgency_level": UrgencyLevel.LEVEL_3,
            "priority_score": 60,
            "doctor_id": None,
            "queued_at": timestamp,
            "called_at": None,
            "completed_at": None,
        },
    )()


def make_doctor(departments: list[str] | None = None):
    return type(
        "Doctor",
        (),
        {
            "doctor_id": "doctor-1",
            "display_name": "Dr. Test",
            "department_ids": departments or ["general-medicine"],
            "available": True,
        },
    )()


def make_user(role: ActorRole, actor_id: str = "doctor-1") -> User:
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


def override_user(user: User):
    app.dependency_overrides[get_current_user] = lambda: user


def override_doctor_repository(doctor=None):
    repository = AsyncMock()
    repository.get_doctor.return_value = doctor
    app.dependency_overrides[get_doctor_repository] = lambda: repository


def override_queue_service(service):
    app.dependency_overrides[get_queue_service] = lambda: service


def test_get_department_queue():
    service = AsyncMock()
    service.get_department_queue.return_value = [
        make_entry("queue-1"),
        make_entry("queue-2"),
    ]

    override_queue_service(service)
    override_user(make_user(ActorRole.DOCTOR))
    override_doctor_repository(make_doctor())

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/departments/general-medicine")

        assert response.status_code == 200
        assert len(response.json()["data"]) == 2
        service.get_department_queue.assert_awaited_once_with(
            "general-medicine")
    finally:
        app.dependency_overrides.clear()


def test_get_department_queue_requires_authentication():
    service = AsyncMock()
    override_queue_service(service)

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/departments/general-medicine")

        assert response.status_code == 401
        service.get_department_queue.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_get_department_queue_rejects_wrong_department():
    service = AsyncMock()
    override_queue_service(service)
    override_user(make_user(ActorRole.DOCTOR))
    override_doctor_repository(make_doctor(["other-department"]))

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/departments/general-medicine")

        assert response.status_code == 403
        service.get_department_queue.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_get_department_queue_allows_admin():
    service = AsyncMock()
    service.get_department_queue.return_value = []

    override_queue_service(service)
    override_user(make_user(ActorRole.ADMIN, "admin-1"))

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/departments/general-medicine")

        assert response.status_code == 200
        assert response.json()["data"] == []
        service.get_department_queue.assert_awaited_once_with(
            "general-medicine")
    finally:
        app.dependency_overrides.clear()


def test_get_queue_entry():
    service = AsyncMock()
    service.get_entry.return_value = make_entry()

    override_queue_service(service)
    override_user(make_user(ActorRole.DOCTOR))
    override_doctor_repository(make_doctor())

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/queue-1")

        assert response.status_code == 200
        assert response.json()["data"]["queue_entry_id"] == "queue-1"
    finally:
        app.dependency_overrides.clear()


def test_get_queue_entry_requires_authentication():
    service = AsyncMock()
    service.get_entry.return_value = make_entry()
    override_queue_service(service)

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/queue-1")

        assert response.status_code == 401
        service.get_entry.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_get_queue_entry_rejects_wrong_department():
    service = AsyncMock()
    service.get_entry.return_value = make_entry()

    override_queue_service(service)
    override_user(make_user(ActorRole.DOCTOR))
    override_doctor_repository(make_doctor(["other-department"]))

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/queue-1")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_queue_entry_not_found():
    service = AsyncMock()
    service.get_entry.return_value = None

    override_queue_service(service)
    override_user(make_user(ActorRole.DOCTOR))
    override_doctor_repository(make_doctor())

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/queue/queue-missing")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
