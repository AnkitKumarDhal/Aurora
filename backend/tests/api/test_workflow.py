from datetime import datetime, timezone
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from backend.api.dependencies import get_workflow_service
from backend.auth.dependencies import get_current_user
from backend.domain.enums import ActorRole, AssignmentStatus, QueueStatus, UrgencyLevel
from backend.domain.user import User
from backend.main import app


def make_queue_entry(doctor_id: str | None = None):
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
            "doctor_id": doctor_id,
            "queued_at": timestamp,
            "called_at": None,
            "completed_at": None,
        },
    )()


def make_assignment(doctor_id: str = "doctor-1"):
    timestamp = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "session-1",
            "doctor_id": doctor_id,
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": timestamp,
            "released_at": None,
        },
    )()


def make_user(role: ActorRole, actor_id: str) -> User:
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
    app.dependency_overrides[get_workflow_service] = lambda: service


def override_user(user: User):
    app.dependency_overrides[get_current_user] = lambda: user


def test_queue_session():
    service = AsyncMock()
    service.queue_session_from_triage.return_value = make_queue_entry()

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/sessions/session-1/queue")

        assert response.status_code == 200
        service.queue_session_from_triage.assert_awaited_once_with("session-1")
    finally:
        app.dependency_overrides.clear()


def test_assign_patient():
    service = AsyncMock()
    service.assign_patient.return_value = make_assignment()

    override_service(service)
    override_user(make_user(ActorRole.ADMIN, "admin-1"))

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/assign")

        assert response.status_code == 200
        service.assign_patient.assert_awaited_once_with("session-1", "queue-1")
    finally:
        app.dependency_overrides.clear()


def test_assign_patient_rejects_doctor():
    service = AsyncMock()
    override_service(service)
    override_user(make_user(ActorRole.DOCTOR, "doctor-1"))

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/assign")

        assert response.status_code == 403
        service.assign_patient.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_assign_patient_requires_authentication():
    service = AsyncMock()
    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/assign")

        assert response.status_code == 401
        service.assign_patient.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_assign_patient_no_doctor():
    service = AsyncMock()
    service.assign_patient.return_value = None

    override_service(service)
    override_user(make_user(ActorRole.ADMIN, "admin-1"))

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/assign")

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_call_patient_rejects_admin():
    service = AsyncMock()
    override_service(service)
    override_user(make_user(ActorRole.ADMIN, "admin-1"))

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/call")

        assert response.status_code == 403
        service.call_patient.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_call_patient_passes_authenticated_doctor():
    service = AsyncMock()
    service.call_patient.return_value = make_queue_entry("doctor-1")

    override_service(service)
    override_user(make_user(ActorRole.DOCTOR, "doctor-1"))

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/queue/queue-1/call")

        assert response.status_code == 200
        service.call_patient.assert_awaited_once_with(
            "session-1",
            "queue-1",
            doctor_id="doctor-1",
        )
    finally:
        app.dependency_overrides.clear()
