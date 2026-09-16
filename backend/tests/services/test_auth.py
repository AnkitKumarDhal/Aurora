from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from backend.auth.service import AuthenticationError, AuthenticationService
from backend.domain.enums import ActorRole
from backend.models.user import UserDocument


def make_document(
    password_hash: str,
    is_active: bool = True,
) -> UserDocument:
    timestamp = datetime.now(timezone.utc)

    return UserDocument(
        user_id="user-1",
        username="doctor",
        password_hash=password_hash,
        role=ActorRole.DOCTOR,
        actor_id="doctor-1",
        is_active=is_active,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_authenticate_valid_credentials():
    repository = AsyncMock()

    service = AuthenticationService(repository)

    password_hash = service.password_hash.hash(
        "password123",
    )

    repository.get_by_username.return_value = (
        make_document(password_hash)
    )

    user = await service.authenticate(
        "doctor",
        "password123",
    )

    assert user.user_id == "user-1"
    assert user.username == "doctor"
    assert user.role == ActorRole.DOCTOR
    assert user.actor_id == "doctor-1"


@pytest.mark.asyncio
async def test_authenticate_invalid_password():
    repository = AsyncMock()
    service = AuthenticationService(repository)

    password_hash = service.password_hash.hash(
        "correct-password",
    )

    repository.get_by_username.return_value = (
        make_document(password_hash)
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid username or password",
    ):
        await service.authenticate(
            "doctor",
            "wrong-password",
        )


@pytest.mark.asyncio
async def test_authenticate_missing_user():
    repository = AsyncMock()
    repository.get_by_username.return_value = None

    service = AuthenticationService(repository)

    with pytest.raises(
        AuthenticationError,
        match="Invalid username or password",
    ):
        await service.authenticate(
            "missing",
            "password123",
        )


@pytest.mark.asyncio
async def test_inactive_user_is_rejected():
    repository = AsyncMock()
    service = AuthenticationService(repository)

    password_hash = service.password_hash.hash(
        "password123",
    )

    repository.get_by_username.return_value = (
        make_document(
            password_hash,
            is_active=False,
        )
    )

    with pytest.raises(
        AuthenticationError,
        match="User account is inactive",
    ):
        await service.authenticate(
            "doctor",
            "password123",
        )


@pytest.mark.asyncio
async def test_access_token_round_trip():
    repository = AsyncMock()
    service = AuthenticationService(repository)

    password_hash = service.password_hash.hash(
        "password123",
    )

    repository.get_by_username.return_value = (
        make_document(password_hash)
    )

    user = await service.authenticate(
        "doctor",
        "password123",
    )

    token = service.create_access_token(user)
    decoded = service.decode_access_token(token)

    assert decoded.user_id == user.user_id
    assert decoded.username == user.username
    assert decoded.role == user.role
    assert decoded.actor_id == user.actor_id


def test_invalid_access_token_is_rejected():
    repository = AsyncMock()
    service = AuthenticationService(repository)

    with pytest.raises(
        AuthenticationError,
        match="Invalid access token",
    ):
        service.decode_access_token("invalid-token")
