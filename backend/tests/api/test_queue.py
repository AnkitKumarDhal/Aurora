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


def make_doctor():
    return type(
        "Doctor",
        (),
        {
            "doctor_id": "doctor-1",
            "display_name": "Dr. Test",
            "department_ids": ["general-medicine"],
            "available": True,
        },
    )()


def make_doctor_user() -> User:
    now = datetime.now(timezone.utc)

    return User(
        user_id="user-doctor-1",
        username="doctor",
        password_hash="",
        role=ActorRole.DOCTOR,
        actor_id="doctor-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def override_doctor():
    app.dependency_overrides[get_current_user] = make_doctor_user

    doctor_repository = AsyncMock()
    doctor_repository.get_doctor.return_value = make_doctor()
    app.dependency_overrides[get_doctor_repository] = lambda: doctor_repository


def test_get_department_queue():
    service = AsyncMock()
    service.get_department_queue.return_value = [
        make_entry("queue-1"),
        make_entry("queue-2"),
    ]

    app.dependency_overrides[get_queue_service] = lambda: service
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/queue/departments/general-medicine"
            )

        assert response.status_code == 200
        assert len(response.json()["data"]) == 2
        assert response.json()["data"][0]["queue_entry_id"] == "queue-1"
        assert response.json()["data"][1]["queue_entry_id"] == "queue-2"

        service.get_department_queue.assert_awaited_once_with(
            "general-medicine"
        )
    finally:
        app.dependency_overrides.clear()


def test_get_empty_department_queue():
    service = AsyncMock()
    service.get_department_queue.return_value = []

    app.dependency_overrides[get_queue_service] = lambda: service
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/queue/departments/general-medicine"
            )

        assert response.status_code == 200
        assert response.json()["data"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_queue_entry():
    service = AsyncMock()
    service.get_entry.return_value = make_entry()

    app.dependency_overrides[get_queue_service] = lambda: service
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/queue/queue-1"
            )

        assert response.status_code == 200
        assert response.json()["data"]["queue_entry_id"] == "queue-1"
        assert response.json()["data"]["session_id"] == "session-1"
        assert response.json()["data"]["status"] == "WAITING"
    finally:
        app.dependency_overrides.clear()


def test_get_queue_entry_not_found():
    service = AsyncMock()
    service.get_entry.return_value = None

    app.dependency_overrides[get_queue_service] = lambda: service
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/queue/queue-missing"
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Queue entry not found"
    finally:
        app.dependency_overrides.clear()
