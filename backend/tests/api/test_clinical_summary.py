from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_assignment_repository, get_clinical_summary_service
from backend.auth.dependencies import get_current_user
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.enums import ActorRole, AssignmentStatus, SummaryStatus
from backend.domain.user import User
from backend.main import app


def make_summary() -> ClinicalSummary:
    now = datetime.now(timezone.utc)

    return ClinicalSummary(
        summary_id="summary_test",
        session_id="session_test",
        status=SummaryStatus.GENERATING,
        chief_complaint="Fever",
        history_of_present_illness="Fever for two days",
        past_medical_history=["Asthma"],
        medications=["Paracetamol"],
        allergies=["Penicillin"],
        relevant_documents=["doc_1"],
        clinical_signals=["fever"],
        generated_at=now,
        created_at=now,
        updated_at=now,
    )


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


def make_assignment():
    now = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "session_test",
            "doctor_id": "doctor-1",
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": now,
            "released_at": None,
        },
    )()


def override_doctor():
    app.dependency_overrides[get_current_user] = make_doctor_user

    assignment_repository = AsyncMock()
    assignment_repository.get_session_assignment.return_value = make_assignment()
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository


def override_summary_service(service):
    app.dependency_overrides[get_clinical_summary_service] = lambda: service


def test_get_summary():
    service = AsyncMock()
    service.get_session_summary.return_value = make_summary()

    override_summary_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session_test/summary")

        assert response.status_code == 200
        assert response.json()["data"]["summary_id"] == "summary_test"
    finally:
        app.dependency_overrides.clear()


def test_get_summary_not_found():
    service = AsyncMock()
    service.get_session_summary.return_value = None

    override_summary_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session_test/summary")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_create_summary():
    service = AsyncMock()
    summary = make_summary()
    service.get_session_summary.return_value = None
    service.create_summary.return_value = summary

    override_summary_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session_test/summary",
                json={
                    "chief_complaint": "Fever",
                    "history_of_present_illness": "Fever for two days",
                    "past_medical_history": ["Asthma"],
                    "medications": ["Paracetamol"],
                    "allergies": ["Penicillin"],
                    "relevant_documents": ["doc_1"],
                    "clinical_signals": ["fever"],
                },
            )

        assert response.status_code == 201
        assert response.json()["data"]["session_id"] == "session_test"
    finally:
        app.dependency_overrides.clear()


def test_create_summary_conflict():
    service = AsyncMock()
    service.get_session_summary.return_value = make_summary()

    override_summary_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session_test/summary",
                json={"chief_complaint": "Fever"},
            )

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_update_summary():
    service = AsyncMock()
    summary = make_summary()
    service.get_session_summary.return_value = summary
    service.update_summary.return_value = summary

    override_summary_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/sessions/session_test/summary",
                json={"chief_complaint": "Severe fever"},
            )

        assert response.status_code == 200
        service.update_summary.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


def test_confirm_summary():
    service = AsyncMock()
    summary = make_summary()
    summary.status = SummaryStatus.CONFIRMED
    summary.confirmed_by = "doctor-1"
    service.confirm_summary.return_value = summary

    override_summary_service(service)
    override_doctor()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session_test/summary/confirm"
            )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "CONFIRMED"
        assert response.json()["data"]["confirmed_by"] == "doctor-1"
        service.confirm_summary.assert_awaited_once_with(
            "session_test",
            "doctor-1",
        )
    finally:
        app.dependency_overrides.clear()
