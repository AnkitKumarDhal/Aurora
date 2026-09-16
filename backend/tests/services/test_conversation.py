from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.database.repositories.conversation import ConversationRepository
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import ConversationInputType, SessionStatus, Speaker
from backend.models.conversation import ConversationTurnDocument
from backend.services.conversation import ConversationService


@pytest.fixture
def repository() -> ConversationRepository:
    repository = AsyncMock(spec=ConversationRepository)
    return repository


@pytest.fixture
def service(
    repository: ConversationRepository,
) -> ConversationService:
    return ConversationService(repository)


@pytest.fixture
def document() -> ConversationTurnDocument:
    timestamp = datetime.now(timezone.utc)

    return ConversationTurnDocument(
        turn_id="turn-1",
        session_id="session-1",
        speaker=Speaker.PATIENT,
        input_type=ConversationInputType.TEXT,
        content="I have had a headache for two days.",
        language="en",
        media_reference=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_turn(
    service: ConversationService,
    repository: ConversationRepository,
    document: ConversationTurnDocument,
) -> None:
    repository.get_turn.return_value = document

    result = await service.get_turn("turn-1")

    assert result is not None
    assert result.turn_id == "turn-1"
    assert result.session_id == "session-1"
    assert result.content == "I have had a headache for two days."

    repository.get_turn.assert_awaited_once_with("turn-1")


@pytest.mark.asyncio
async def test_get_turn_missing(
    service: ConversationService,
    repository: ConversationRepository,
) -> None:
    repository.get_turn.return_value = None

    result = await service.get_turn("missing")

    assert result is None


@pytest.mark.asyncio
async def test_get_session_turns(
    service: ConversationService,
    repository: ConversationRepository,
    document: ConversationTurnDocument,
) -> None:
    repository.get_session_turns.return_value = [document]

    result = await service.get_session_turns("session-1")

    assert len(result) == 1
    assert result[0].turn_id == "turn-1"

    repository.get_session_turns.assert_awaited_once_with("session-1")


@pytest.mark.asyncio
async def test_add_turn(
    service: ConversationService,
    repository: ConversationRepository,
) -> None:
    timestamp = datetime.now(timezone.utc)

    turn = ConversationTurn(
        turn_id="turn-1",
        session_id="session-1",
        speaker=Speaker.PATIENT,
        input_type=ConversationInputType.TEXT,
        content="I have a headache.",
        language="en",
        media_reference=None,
        created_at=timestamp,
        updated_at=timestamp,
    )

    result = await service.add_turn(turn)

    assert result is turn
    repository.create_turn.assert_awaited_once()

    created_document = repository.create_turn.await_args.args[0]

    assert created_document.turn_id == "turn-1"
    assert created_document.session_id == "session-1"
    assert created_document.content == "I have a headache."


@pytest.mark.asyncio
async def test_submit_first_turn_moves_session_to_history() -> None:
    repository = AsyncMock(spec=ConversationRepository)
    session_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.CONSENTED
    session_service.get_session.return_value = session

    transitioned = AsyncMock()
    transitioned.status = SessionStatus.HISTORY_IN_PROGRESS
    session_service.transition_session.return_value = transitioned

    service = ConversationService(
        repository=repository,
        session_service=session_service,
    )

    turn = ConversationTurn(
        turn_id="turn-1",
        session_id="session-1",
        speaker=Speaker.PATIENT,
        input_type=ConversationInputType.TEXT,
        content="I have a headache.",
        language="en",
        media_reference=None,
    )

    result = await service.submit_turn(turn)

    assert result is turn
    session_service.transition_session.assert_awaited_once_with(
        "session-1",
        SessionStatus.HISTORY_IN_PROGRESS,
    )
    repository.create_turn.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_turn_in_history_does_not_transition() -> None:
    repository = AsyncMock(spec=ConversationRepository)
    session_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.HISTORY_IN_PROGRESS
    session_service.get_session.return_value = session

    service = ConversationService(
        repository=repository,
        session_service=session_service,
    )

    turn = ConversationTurn(
        turn_id="turn-1",
        session_id="session-1",
        speaker=Speaker.PATIENT,
        input_type=ConversationInputType.TEXT,
        content="Still having the headache.",
        language="en",
        media_reference=None,
    )

    result = await service.submit_turn(turn)

    assert result is turn
    session_service.transition_session.assert_not_awaited()
    repository.create_turn.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_turn_requires_consent() -> None:
    repository = AsyncMock(spec=ConversationRepository)
    session_service = AsyncMock()

    session = AsyncMock()
    session.status = SessionStatus.IDENTIFYING
    session_service.get_session.return_value = session

    service = ConversationService(
        repository=repository,
        session_service=session_service,
    )

    turn = ConversationTurn(
        turn_id="turn-1",
        session_id="session-1",
        speaker=Speaker.PATIENT,
        input_type=ConversationInputType.TEXT,
        content="I have a headache.",
        language="en",
        media_reference=None,
    )

    with pytest.raises(
        ValueError,
        match="Session must be consented or have history in progress",
    ):
        await service.submit_turn(turn)

    repository.create_turn.assert_not_awaited()
