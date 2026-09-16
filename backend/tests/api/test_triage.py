from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_assignment_repository, get_triage_service
from backend.auth.dependencies import get_current_user
from backend.domain.enums import ActorRole, AssignmentStatus, TriageStatus, UrgencyLevel
from backend.domain.user import User
from backend.main import app


def make_user(role: ActorRole = ActorRole.DOCTOR, actor_id: str = "doctor-1") -> User:
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


def make_assignment(doctor_id: str = "doctor-1"):
    now = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "session-1",
            "doctor_id": doctor_id,
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": now,
            "released_at": None,
        },
    )()


def make_result():
    timestamp = datetime.now(timezone.utc)

    return type(
        "TriageResult",
        (),
        {
            "triage_id": "triage-1",
            "session_id": "session-1",
            "status": TriageStatus.PENDING,
            "urgency_level": None,
            "priority_score": None,
            "red_flags_present": False,
            "assessed_at": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )()


def make_assessed_result():
    timestamp = datetime.now(timezone.utc)

    return type(
        "TriageResult",
        (),
        {
            "triage_id": "triage-1",
            "session_id": "session-1",
            "status": TriageStatus.ASSESSED,
            "urgency_level": UrgencyLevel.LEVEL_5,
            "priority_score": 100,
            "red_flags_present": True,
            "assessed_at": timestamp,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )()


def make_signal():
    timestamp = datetime.now(timezone.utc)

    return type(
        "ClinicalSignal",
        (),
        {
            "signal_id": "signal-1",
            "session_id": "session-1",
            "signal_type": None,
            "name": "severe_chest_pain",
            "value": True,
            "confidence": 1.0,
            "source": "ai",
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )()


def override_service(service):
    app.dependency_overrides[get_triage_service] = lambda: service


def override_doctor(doctor_id: str = "doctor-1"):
    app.dependency_overrides[get_current_user] = lambda: make_user(
        ActorRole.DOCTOR,
        doctor_id,
    )

    assignment_repository = AsyncMock()
    assignment_repository.get_session_assignment.return_value = make_assignment(
        doctor_id,
    )
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository


def test_get_triage():
    service = AsyncMock()
    service.get_session_result.return_value = make_assessed_result()

    override_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session-1/triage")

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ASSESSED"
        assert response.json()["data"]["urgency_level"] == 5
        assert response.json()["data"]["priority_score"] == 100
        assert response.json()["data"]["red_flags_present"] is True
        service.get_session_result.assert_awaited_once_with("session-1")
    finally:
        app.dependency_overrides.clear()


def test_get_triage_requires_authentication():
    service = AsyncMock()

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session-1/triage")

        assert response.status_code == 401
        service.get_session_result.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_get_triage_rejects_unassigned_doctor():
    service = AsyncMock()

    override_service(service)
    override_doctor("doctor-2")

    app.dependency_overrides[get_assignment_repository] = lambda: (
        type(
            "AssignmentRepository",
            (),
            {
                "get_session_assignment": AsyncMock(
                    return_value=make_assignment("doctor-1")
                )
            },
        )()
    )

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session-1/triage")

        assert response.status_code == 403
        service.get_session_result.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_get_triage_not_found():
    service = AsyncMock()
    service.get_session_result.return_value = None

    override_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session-1/triage")

        assert response.status_code == 404
        assert response.json()["detail"] == "Triage result not found"
    finally:
        app.dependency_overrides.clear()


def test_assess_triage_uses_clinical_signals():
    service = AsyncMock()
    service.get_session_signals.return_value = [make_signal()]
    service.get_session_result.return_value = make_result()
    service.assess_from_signals.return_value = make_assessed_result()

    override_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/triage",
                json={},
            )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ASSESSED"
        assert response.json()["data"]["urgency_level"] == 5
        assert response.json()["data"]["priority_score"] == 100

        service.assess_from_signals.assert_awaited_once_with(
            "triage-1",
            service.get_session_signals.return_value,
        )
    finally:
        app.dependency_overrides.clear()


def test_assess_triage_requires_authentication():
    service = AsyncMock()

    override_service(service)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/triage",
                json={},
            )

        assert response.status_code == 401
        service.get_session_signals.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_assess_triage_rejects_unassigned_doctor():
    service = AsyncMock()

    override_service(service)
    app.dependency_overrides[get_current_user] = lambda: make_user(
        ActorRole.DOCTOR,
        "doctor-1",
    )

    assignment_repository = AsyncMock()
    assignment_repository.get_session_assignment.return_value = make_assignment(
        "doctor-2",
    )
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/triage",
                json={},
            )

        assert response.status_code == 403
        service.get_session_signals.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_assess_triage_missing_signals():
    service = AsyncMock()
    service.get_session_signals.return_value = None

    override_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/triage",
                json={},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Clinical signals not found"
    finally:
        app.dependency_overrides.clear()


def test_assess_triage_missing_result():
    service = AsyncMock()
    service.get_session_signals.return_value = [make_signal()]
    service.get_session_result.return_value = None

    override_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/triage",
                json={},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Triage result not found"
    finally:
        app.dependency_overrides.clear()
