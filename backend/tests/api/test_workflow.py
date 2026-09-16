from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_workflow_service
from backend.domain.enums import AssignmentStatus, QueueStatus, UrgencyLevel
from backend.main import app


def make_queue_entry():
    timestamp = datetime.now(timezone.utc)

    return type(
        "QueueEntry",
        (),
        {
            "queue_entry_id": "queue-1",
            "session_id": "session-1",
            "department_id": "general-medicine",
            "status": QueueStatus.WAITING,
            "position": 1,
            "urgency_level": UrgencyLevel.LEVEL_4,
            "priority_score": 80,
            "doctor_id": None,
            "queued_at": timestamp,
            "called_at": None,
            "completed_at": None,
        },
    )()


def make_assignment():
    timestamp = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "session-1",
            "doctor_id": "doctor-1",
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": timestamp,
            "released_at": None,
        },
    )()


def test_queue_session():
    service = AsyncMock()
    service.queue_session_from_triage.return_value = make_queue_entry()

    app.dependency_overrides[get_workflow_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue"
            )

        assert response.status_code == 200
        assert response.json()[
            "data"]["queue_entry"]["queue_entry_id"] == "queue-1"
        assert response.json()["data"]["queue_entry"]["priority_score"] == 80
        service.queue_session_from_triage.assert_awaited_once_with(
            "session-1"
        )
    finally:
        app.dependency_overrides.clear()


def test_assign_patient():
    service = AsyncMock()
    service.assign_patient.return_value = make_assignment()

    app.dependency_overrides[get_workflow_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/assign"
            )

        assert response.status_code == 200
        assert response.json()["data"]["assignment"]["doctor_id"] == "doctor-1"
    finally:
        app.dependency_overrides.clear()


def test_assign_patient_no_doctor():
    service = AsyncMock()
    service.assign_patient.return_value = None

    app.dependency_overrides[get_workflow_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/assign"
            )

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()
