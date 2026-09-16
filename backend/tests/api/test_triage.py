from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_triage_service
from backend.domain.enums import TriageStatus, UrgencyLevel
from backend.main import app


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


def test_get_triage():
    service = AsyncMock()
    service.get_session_result.return_value = make_assessed_result()

    app.dependency_overrides[get_triage_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/sessions/session-1/triage"
            )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ASSESSED"
        assert response.json()["data"]["urgency_level"] == 5
        assert response.json()["data"]["priority_score"] == 100
        assert response.json()["data"]["red_flags_present"] is True
    finally:
        app.dependency_overrides.clear()


def test_get_triage_not_found():
    service = AsyncMock()
    service.get_session_result.return_value = None

    app.dependency_overrides[get_triage_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/sessions/session-1/triage"
            )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_assess_triage_uses_clinical_signals():
    service = AsyncMock()

    service.get_session_signals.return_value = [make_signal()]
    service.get_session_result.return_value = make_result()
    service.assess_from_signals.return_value = make_assessed_result()

    app.dependency_overrides[get_triage_service] = lambda: service

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


def test_assess_triage_missing_signals():
    service = AsyncMock()

    service.get_session_signals.return_value = None

    app.dependency_overrides[get_triage_service] = lambda: service

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

    app.dependency_overrides[get_triage_service] = lambda: service

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
