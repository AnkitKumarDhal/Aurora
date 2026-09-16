from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_clinical_summary_service
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.enums import SummaryStatus
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


def test_get_summary() -> None:
    service = AsyncMock()
    service.get_session_summary.return_value = make_summary()

    app.dependency_overrides[get_clinical_summary_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session_test/summary")

        assert response.status_code == 200
        assert response.json()["data"]["summary_id"] == "summary_test"
    finally:
        app.dependency_overrides.clear()


def test_get_summary_not_found() -> None:
    service = AsyncMock()
    service.get_session_summary.return_value = None

    app.dependency_overrides[get_clinical_summary_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/sessions/session_test/summary")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_create_summary() -> None:
    service = AsyncMock()
    summary = make_summary()
    service.get_session_summary.return_value = None
    service.create_summary.return_value = summary

    app.dependency_overrides[get_clinical_summary_service] = lambda: service

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


def test_create_summary_conflict() -> None:
    service = AsyncMock()
    service.get_session_summary.return_value = make_summary()

    app.dependency_overrides[get_clinical_summary_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session_test/summary",
                json={"chief_complaint": "Fever"},
            )

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_update_summary() -> None:
    service = AsyncMock()
    summary = make_summary()
    service.get_session_summary.return_value = summary
    service.update_summary.return_value = summary

    app.dependency_overrides[get_clinical_summary_service] = lambda: service

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


def test_confirm_summary() -> None:
    service = AsyncMock()
    summary = make_summary()
    summary.status = SummaryStatus.CONFIRMED
    summary.confirmed_by = "doctor_1"
    service.confirm_summary.return_value = summary

    app.dependency_overrides[get_clinical_summary_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session_test/summary/confirm",
                params={"doctor_id": "doctor_1"},
            )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "CONFIRMED"
        assert response.json()["data"]["confirmed_by"] == "doctor_1"
    finally:
        app.dependency_overrides.clear()
