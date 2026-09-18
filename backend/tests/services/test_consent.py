from unittest.mock import AsyncMock

import pytest

from backend.domain.enums import (
    ConsentStatus,
    SessionStatus,
    VerificationStatus,
)
from backend.services.consent import ConsentService


def make_session(
    status: SessionStatus = SessionStatus.IDENTIFYING,
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
) -> AsyncMock:
    session = AsyncMock()
    session.status = status
    session.verification_status = verification_status
    session.consent_status = ConsentStatus.PENDING
    return session


@pytest.mark.asyncio
async def test_grant_consent_persists_identity() -> None:
    session_service = AsyncMock()
    verification_service = AsyncMock()

    session = make_session()
    session_service.get_session.return_value = session

    updated_session = make_session(
        status=SessionStatus.IDENTIFYING,
    )
    session_service.set_consent.return_value = updated_session

    consented_session = make_session(
        status=SessionStatus.CONSENTED,
    )
    session_service.transition_session.return_value = (
        consented_session
    )

    service = ConsentService(
        session_service=session_service,
        verification_service=verification_service,
    )

    result = await service.grant(
        "session-1",
        "1.0",
        "ABHA",
        "11112222333344",
    )

    assert result == SessionStatus.CONSENTED

    verification_service.persist_identity.assert_awaited_once_with(
        "session-1",
        "ABHA",
        "11112222333344",
    )
    session_service.set_consent.assert_awaited_once_with(
        "session-1",
        ConsentStatus.GRANTED,
    )
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.CONSENTED,
    )


@pytest.mark.asyncio
async def test_deny_consent_does_not_persist_identity() -> None:
    session_service = AsyncMock()
    verification_service = AsyncMock()

    session = make_session()
    session_service.get_session.return_value = session
    session_service.set_consent.return_value = session

    service = ConsentService(
        session_service=session_service,
        verification_service=verification_service,
    )

    result = await service.deny(
        "session-1",
        "1.0",
    )

    assert result == SessionStatus.IDENTIFYING
    verification_service.persist_identity.assert_not_awaited()
    session_service.set_consent.assert_awaited_once_with(
        "session-1",
        ConsentStatus.DENIED,
    )
    session_service.transition_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_consent_requires_verified_identity() -> None:
    session_service = AsyncMock()
    verification_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        verification_status=VerificationStatus.PENDING,
    )

    service = ConsentService(
        session_service=session_service,
        verification_service=verification_service,
    )

    with pytest.raises(
        ValueError,
        match="Patient identity must be verified before consent",
    ):
        await service.grant(
            "session-1",
            "1.0",
            "ABHA",
            "11112222333344",
        )

    verification_service.persist_identity.assert_not_awaited()


@pytest.mark.asyncio
async def test_consent_requires_identifying_session() -> None:
    session_service = AsyncMock()
    verification_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        status=SessionStatus.CREATED,
    )

    service = ConsentService(
        session_service=session_service,
        verification_service=verification_service,
    )

    with pytest.raises(
        ValueError,
        match="Session must be identifying before consent",
    ):
        await service.grant(
            "session-1",
            "1.0",
            "ABHA",
            "11112222333344",
        )

    verification_service.persist_identity.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejects_unsupported_consent_version() -> None:
    session_service = AsyncMock()
    verification_service = AsyncMock()

    service = ConsentService(
        session_service=session_service,
        verification_service=verification_service,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported consent version",
    ):
        await service.grant(
            "session-1",
            "2.0",
            "ABHA",
            "11112222333344",
        )

    session_service.get_session.assert_not_awaited()
    verification_service.persist_identity.assert_not_awaited()


@pytest.mark.asyncio
async def test_grant_consent_is_idempotent_after_completion() -> None:
    session_service = AsyncMock()
    verification_service = AsyncMock()

    session = make_session(
        status=SessionStatus.CONSENTED,
    )
    session.consent_status = ConsentStatus.GRANTED
    session_service.get_session.return_value = session

    service = ConsentService(
        session_service=session_service,
        verification_service=verification_service,
    )

    result = await service.grant(
        "session-1",
        "1.0",
        "ABHA",
        "11112222333344",
    )

    assert result == SessionStatus.CONSENTED
    verification_service.persist_identity.assert_not_awaited()
    session_service.set_consent.assert_not_awaited()
    session_service.transition_session.assert_not_awaited()
