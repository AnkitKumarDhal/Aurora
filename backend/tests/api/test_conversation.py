from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api.dependencies import get_assignment_repository, get_conversation_service
from backend.auth.dependencies import get_current_user
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import ActorRole, AssignmentStatus, ConversationInputType, Speaker
from backend.domain.user import User
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


def build_user(actor_id: str = "doctor-1") -> User:
    now = datetime.now(timezone.utc)

    return User(
        user_id=f"user-{actor_id}",
        username=actor_id,
        password_hash="",
        role=ActorRole.DOCTOR,
        actor_id=actor_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def build_assignment(doctor_id: str = "doctor-1"):
    now = datetime.now(timezone.utc)

    return type(
        "Assignment",
        (),
        {
            "assignment_id": "assignment-1",
            "session_id": "sess-test",
            "doctor_id": doctor_id,
            "department_id": "general-medicine",
            "status": AssignmentStatus.ACTIVE,
            "assigned_at": now,
            "released_at": None,
        },
    )()


def override_service(service: AsyncMock) -> None:
    app.dependency_overrides[get_conversation_service] = lambda: service


def override_doctor(doctor_id: str = "doctor-1") -> None:
    app.dependency_overrides[get_current_user] = lambda: build_user(doctor_id)

    assignment_repository = AsyncMock()
    assignment_repository.get_session_assignment.return_value = build_assignment(
        doctor_id
    )
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_submit_conversation_turn() -> None:
    service = AsyncMock()
    service.submit_turn.return_value = build_turn()
    override_service(service)

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
    assert response.json()[
        "data"]["content"] == "I have had a headache for two days."

    submitted_turn = service.submit_turn.await_args.args[0]
    assert submitted_turn.session_id == "sess-test"
    assert submitted_turn.speaker == Speaker.PATIENT


def test_submit_conversation_turn_requires_content_or_media() -> None:
    service = AsyncMock()
    override_service(service)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/sessions/sess-test/conversation/turns",
            json={"input_type": "TEXT", "language": "en"},
        )

    assert response.status_code == 422
    service.submit_turn.assert_not_awaited()


def test_submit_conversation_turn_rejects_invalid_session_state() -> None:
    service = AsyncMock()
    service.submit_turn.side_effect = ValueError(
        "Session must be consented or have history in progress",
    )
    override_service(service)

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
    assert response.json()[
        "detail"] == "Session must be consented or have history in progress"


def test_get_conversation_history() -> None:
    service = AsyncMock()
    service.get_session_turns.return_value = [build_turn()]
    override_service(service)
    override_doctor()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/conversation/turns",
        )

    assert response.status_code == 200
    assert len(response.json()["data"]["turns"]) == 1
    assert response.json()["data"]["turns"][0]["turn_id"] == "turn-test"


def test_get_conversation_requires_authentication() -> None:
    service = AsyncMock()
    override_service(service)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/conversation/turns"
        )

    assert response.status_code == 401
    service.get_session_turns.assert_not_awaited()


def test_get_conversation_rejects_unassigned_doctor() -> None:
    service = AsyncMock()
    assignment_repository = AsyncMock()
    assignment_repository.get_session_assignment.return_value = build_assignment(
        "doctor-2"
    )

    override_service(service)
    app.dependency_overrides[get_current_user] = lambda: build_user("doctor-1")
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sessions/sess-test/conversation/turns"
        )

    assert response.status_code == 403
    service.get_session_turns.assert_not_awaited()
