from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_conversation_service
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import ConversationInputType, Speaker
from backend.main import app


def build_turn(session_id: str = "sess-test") -> ConversationTurn:
    return ConversationTurn(
        turn_id="turn-test",
        session_id=session_id,
        speaker=Speaker.PATIENT,
        input_type=ConversationInputType.TEXT,
        content="I have had a headache for two days.",
        language="en",
    )


def override_service() -> AsyncMock:
    service = AsyncMock()
    app.dependency_overrides[get_conversation_service] = lambda: service
    return service


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_submit_conversation_turn() -> None:
    service = override_service()
    service.submit_turn.return_value = build_turn()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/sessions/sess-test/conversation/turns",
            json={
                "input_type": "TEXT",
                "content": "I have had a headache for two days.",
                "language": "en",
            },
        )

    assert response.status_code == 201
    assert response.json()["data"]["session_id"] == "sess-test"
    assert response.json()["data"]["speaker"] == "patient"
    assert response.json()["data"]["content"] == (
        "I have had a headache for two days."
    )

    submitted_turn = service.submit_turn.await_args.args[0]
    assert submitted_turn.session_id == "sess-test"
    assert submitted_turn.speaker == Speaker.PATIENT


def test_submit_conversation_turn_requires_content_or_media() -> None:
    service = override_service()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/sessions/sess-test/conversation/turns",
            json={"input_type": "TEXT", "language": "en"},
        )

    assert response.status_code == 422
    service.submit_turn.assert_not_awaited()


def test_submit_conversation_turn_rejects_invalid_session_state() -> None:
    service = override_service()
    service.submit_turn.side_effect = ValueError(
        "Session must be consented or have history in progress",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/sessions/sess-test/conversation/turns",
            json={
                "input_type": "TEXT",
                "content": "I have a headache.",
                "language": "en",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Session must be consented or have history in progress"
    )


def test_get_conversation_history() -> None:
    service = override_service()
    service.get_session_turns.return_value = [build_turn()]

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/conversation/turns",
        )

    assert response.status_code == 200
    assert len(response.json()["data"]["turns"]) == 1
    assert response.json()["data"]["turns"][0]["turn_id"] == "turn-test"
