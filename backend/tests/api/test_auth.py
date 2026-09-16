from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from backend.api.dependencies import get_authentication_service
from backend.main import app


def test_login():
    service = MagicMock()

    user = type(
        "User",
        (),
        {
            "user_id": "user-1",
            "username": "doctor",
            "role": "DOCTOR",
            "actor_id": "doctor-1",
        },
    )()

    service.authenticate = AsyncMock(
        return_value=user,
    )
    service.create_access_token.return_value = "token-123"

    app.dependency_overrides[
        get_authentication_service
    ] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": "doctor",
                    "password": "password123",
                },
            )

        assert response.status_code == 200
        assert (
            response.json()["data"]["access_token"]
            == "token-123"
        )

        service.authenticate.assert_awaited_once_with(
            "doctor",
            "password123",
        )
        service.create_access_token.assert_called_once_with(
            user,
        )
    finally:
        app.dependency_overrides.pop(
            get_authentication_service,
            None,
        )
