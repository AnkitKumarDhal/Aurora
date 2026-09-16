# backend/tests/api/test_intake.py

from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_intake_service
from backend.domain.enums import SessionStatus
from backend.main import app


def make_session(status: SessionStatus):
    return type(
        "Session",
        (),
        {
            "session_id": "session-1",
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        },
    )()


def test_finalize_intake():
    service = AsyncMock()
    service.finalize.return_value = make_session(
        SessionStatus.SUMMARY_READY
    )

    app.dependency_overrides[get_intake_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/finalize"
            )

        assert response.status_code == 200
        assert response.json()["data"]["session_id"] == "session-1"
        assert response.json()["data"]["status"] == "SUMMARY_READY"
        service.finalize.assert_awaited_once_with("session-1")
    finally:
        app.dependency_overrides.clear()


def test_finalize_intake_missing_session():
    service = AsyncMock()
    service.finalize.side_effect = ValueError(
        "Clinical session not found"
    )

    app.dependency_overrides[get_intake_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/finalize"
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Clinical session not found"
    finally:
        app.dependency_overrides.clear()


def test_finalize_intake_missing_summary():
    service = AsyncMock()
    service.finalize.side_effect = ValueError(
        "Clinical summary not found"
    )

    app.dependency_overrides[get_intake_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/finalize"
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Clinical summary not found"
    finally:
        app.dependency_overrides.clear()


def test_finalize_intake_invalid_state():
    service = AsyncMock()
    service.finalize.side_effect = ValueError(
        "Session is not ready for intake finalization"
    )

    app.dependency_overrides[get_intake_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/sessions/session-1/finalize"
            )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Session is not ready for intake finalization"
        )
    finally:
        app.dependency_overrides.clear()
