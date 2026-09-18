from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from backend.domain.clinical_session import ClinicalSession
from backend.main import app
from backend.api.dependencies import get_clinical_session_service


@pytest.fixture
def service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def override_service(service: AsyncMock):
    app.dependency_overrides[get_clinical_session_service] = lambda: service
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_session(service: AsyncMock) -> None:
    timestamp = datetime.now(timezone.utc)
    service.create_session.return_value = ClinicalSession(
        session_id="sess_test",
        patient_id="unverified",
        department_id="general-medicine",
        created_at=timestamp,
        updated_at=timestamp,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/sessions",
            json={"department_id": "general-medicine"},
        )

    assert response.status_code == 201

    body = response.json()
    assert body["data"]["session_id"] == "sess_test"
    assert body["data"]["status"] == "CREATED"
    assert body["data"]["department_id"] == "general-medicine"

    service.create_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session(service: AsyncMock) -> None:
    timestamp = datetime.now(timezone.utc)
    service.get_session.return_value = ClinicalSession(
        session_id="sess_test",
        patient_id="unverified",
        department_id="general-medicine",
        created_at=timestamp,
        updated_at=timestamp,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/sessions/sess_test")

    assert response.status_code == 200
    assert response.json()["data"]["session_id"] == "sess_test"

    service.get_session.assert_awaited_once_with("sess_test")


@pytest.mark.asyncio
async def test_get_session_not_found(service: AsyncMock) -> None:
    service.get_session.return_value = None

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/sessions/missing")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_abandon_session(service: AsyncMock) -> None:
    timestamp = datetime.now(timezone.utc)
    session = ClinicalSession(
        session_id="sess_test",
        patient_id="patient_test",
        department_id="general-medicine",
        status="ABANDONED",
        created_at=timestamp,
        updated_at=timestamp,
    )
    service.abandon_session.return_value = session

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/sessions/sess_test/abandon",
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ABANDONED"
    service.abandon_session.assert_awaited_once_with("sess_test")


@pytest.mark.asyncio
async def test_abandon_session_not_found(service: AsyncMock) -> None:
    service.abandon_session.return_value = None

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/sessions/missing/abandon",
        )

    assert response.status_code == 404
