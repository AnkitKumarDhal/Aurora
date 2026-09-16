# backend/tests/services/test_intake.py

from unittest.mock import AsyncMock

import pytest

from backend.domain.enums import SessionStatus
from backend.services.intake import IntakeService


def make_session(status: SessionStatus):
    return type(
        "Session",
        (),
        {
            "session_id": "session-1",
            "status": status,
        },
    )()


@pytest.mark.asyncio
async def test_finalize_transitions_history_session_to_summary_ready():
    session_service = AsyncMock()
    summary_service = AsyncMock()

    session = make_session(SessionStatus.HISTORY_IN_PROGRESS)

    session_service.get_session.return_value = session
    summary_service.get_session_summary.return_value = object()
    session_service.transition_session.return_value = make_session(
        SessionStatus.SUMMARY_READY
    )

    service = IntakeService(session_service, summary_service)

    result = await service.finalize("session-1")

    assert result.status == SessionStatus.SUMMARY_READY
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.SUMMARY_READY,
    )


@pytest.mark.asyncio
async def test_finalize_transitions_document_processing_session():
    session_service = AsyncMock()
    summary_service = AsyncMock()

    session = make_session(SessionStatus.DOCUMENT_PROCESSING)

    session_service.get_session.return_value = session
    summary_service.get_session_summary.return_value = object()
    session_service.transition_session.return_value = make_session(
        SessionStatus.SUMMARY_READY
    )

    service = IntakeService(session_service, summary_service)

    result = await service.finalize("session-1")

    assert result.status == SessionStatus.SUMMARY_READY


@pytest.mark.asyncio
async def test_finalize_requires_existing_session():
    session_service = AsyncMock()
    summary_service = AsyncMock()

    session_service.get_session.return_value = None

    service = IntakeService(session_service, summary_service)

    with pytest.raises(ValueError, match="Clinical session not found"):
        await service.finalize("session-1")

    summary_service.get_session_summary.assert_not_awaited()
    session_service.transition_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalize_requires_existing_summary():
    session_service = AsyncMock()
    summary_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.HISTORY_IN_PROGRESS
    )
    summary_service.get_session_summary.return_value = None

    service = IntakeService(session_service, summary_service)

    with pytest.raises(ValueError, match="Clinical summary not found"):
        await service.finalize("session-1")

    session_service.transition_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalize_rejects_invalid_session_state():
    session_service = AsyncMock()
    summary_service = AsyncMock()

    session_service.get_session.return_value = make_session(
        SessionStatus.CREATED
    )
    summary_service.get_session_summary.return_value = object()

    service = IntakeService(session_service, summary_service)

    with pytest.raises(
        ValueError,
        match="Session is not ready for intake finalization",
    ):
        await service.finalize("session-1")

    session_service.transition_session.assert_not_awaited()
