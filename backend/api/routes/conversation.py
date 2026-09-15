from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_conversation_service
from backend.api.schemas.conversation import (
    ConversationTurnRequest,
    ConversationTurnResponse,
)
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import ConversationInputType, Speaker
from backend.services.conversation import ConversationService

router = APIRouter(
    prefix="/sessions/{session_id}/conversation",
    tags=["conversation"],
)


@router.post("/turns", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submit_turn(
    session_id: str,
    request: ConversationTurnRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> dict:
    if request.input_type in {
        ConversationInputType.TEXT,
        ConversationInputType.GUIDED_INPUT,
    } and not request.content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Content is required for text and guided input",
        )

    if request.input_type == ConversationInputType.AUDIO and not request.media_reference:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Media reference is required for audio input",
        )

    turn = ConversationTurn(
        turn_id=f"turn_{uuid4().hex}",
        session_id=session_id,
        speaker=Speaker.PATIENT,
        input_type=request.input_type,
        content=request.content,
        language=request.language,
        media_reference=request.media_reference,
    )

    try:
        created_turn = await service.submit_turn(turn)
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if message == "Clinical session not found"
                else status.HTTP_400_BAD_REQUEST
            ),
            detail=message,
        ) from exc

    response = ConversationTurnResponse(
        turn_id=created_turn.turn_id,
        speaker=created_turn.speaker.value,
        input_type=created_turn.input_type,
        content=created_turn.content,
        language=created_turn.language,
        media_reference=created_turn.media_reference,
        created_at=created_turn.created_at,
    )

    return {
        "data": response.model_dump(mode="json"),
        "meta": {
            "status": "RECEIVED",
        },
    }


@router.get("", response_model=dict)
async def get_conversation(
    session_id: str,
    service: ConversationService = Depends(get_conversation_service),
) -> dict:
    turns = await service.get_session_turns(session_id)

    return {
        "data": {
            "turns": [
                ConversationTurnResponse(
                    turn_id=turn.turn_id,
                    speaker=turn.speaker.value,
                    input_type=turn.input_type,
                    content=turn.content,
                    language=turn.language,
                    media_reference=turn.media_reference,
                    created_at=turn.created_at,
                ).model_dump(mode="json")
                for turn in turns
            ],
        },
    }
