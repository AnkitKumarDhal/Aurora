from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_conversation_service
from backend.api.schemas.conversation import (
    ConversationHistoryResponse,
    ConversationTurnRequest,
    ConversationTurnResponse,
)
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import Speaker
from backend.services.conversation import ConversationService

router = APIRouter(
    prefix="/sessions/{session_id}/conversation",
    tags=["conversation"],
)


@router.post(
    "/turns",
    response_model=dict[str, ConversationTurnResponse],
    status_code=status.HTTP_201_CREATED,
)
async def submit_turn(
    session_id: str,
    request: ConversationTurnRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, ConversationTurnResponse]:
    if request.content is None and request.media_reference is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="content or media_reference is required",
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
        result = await service.submit_turn(turn)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "data": ConversationTurnResponse(
            turn_id=result.turn_id,
            session_id=result.session_id,
            speaker=result.speaker.value.lower(),
            input_type=result.input_type,
            content=result.content,
            language=result.language,
            media_reference=result.media_reference,
            created_at=result.created_at,
        ),
    }


@router.get(
    "/turns",
    response_model=dict[str, ConversationHistoryResponse],
)
async def get_conversation(
    session_id: str,
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, ConversationHistoryResponse]:
    turns = await service.get_session_turns(session_id)

    return {
        "data": ConversationHistoryResponse(
            turns=[
                ConversationTurnResponse(
                    turn_id=turn.turn_id,
                    session_id=turn.session_id,
                    speaker=turn.speaker.value.lower(),
                    input_type=turn.input_type,
                    content=turn.content,
                    language=turn.language,
                    media_reference=turn.media_reference,
                    created_at=turn.created_at,
                )
                for turn in turns
            ],
        ),
    }
