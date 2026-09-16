# backend/tests/api/test_queue.py

from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_queue_service
from backend.domain.enums import QueueStatus, UrgencyLevel
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


def test_get_department_queue():
    service = AsyncMock()
    service.get_department_queue.return_value = [
        make_entry("queue-1"),
        make_entry("queue-2"),
    ]

    app.dependency_overrides[get_queue_service] = lambda: service

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

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/queue/queue-missing"
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Queue entry not found"
    finally:
        app.dependency_overrides.clear()
