from __future__ import annotations

from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.dependencies import get_interview_controller
from backend.api.schemas.interview import InterviewFinalizeResponse, InterviewStateResponse, InterviewTurnRequest, InterviewTurnResponse
from backend.ai.interview.controller import InterviewController

router = APIRouter(
    prefix="/sessions/{session_id}/interview", tags=["interview"])


@router.get("", response_model=dict[str, InterviewStateResponse])
async def get_interview_state(session_id: str, language: str | None = Query(default=None, min_length=2, max_length=16), controller: InterviewController = Depends(get_interview_controller)) -> dict[str, InterviewStateResponse]:
    try:
        result = await controller.get_state(session_id, language=language)
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if message ==
                            "Clinical session not found" else status.HTTP_400_BAD_REQUEST, detail=message) from exc
    return {"data": InterviewStateResponse(**result)}


@router.post("/turns", response_model=dict[str, InterviewTurnResponse], status_code=status.HTTP_201_CREATED)
async def process_interview_turn(session_id: str, request: InterviewTurnRequest, controller: InterviewController = Depends(get_interview_controller)) -> dict[str, InterviewTurnResponse]:
    expected_session_id = f"sess_{
        sha256(request.draft_id.encode()).hexdigest()[:24]}"
    if session_id != expected_session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Draft does not match interview session")
    turn_id = "turn_" + \
        sha256(f"{request.draft_id}:{
               request.client_turn_id}".encode()).hexdigest()
    try:
        result = await controller.process_turn(session_id=session_id, content=request.content, input_type=request.input_type, language=request.language, turn_id=turn_id)
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if message ==
                            "Clinical session not found" else status.HTTP_400_BAD_REQUEST, detail=message) from exc
    turn = result["turn"]
    return {"data": InterviewTurnResponse(turn_id=turn.turn_id, session_id=turn.session_id, speaker=turn.speaker.value.lower(), input_type=turn.input_type, content=turn.content or "", language=turn.language, created_at=turn.created_at, assistant_response=result["assistant_response"], next_question=result["next_question"], completed=result["completed"], topic=result["topic"], known_fields=result["known_fields"], extracted_fields=result["extracted_fields"], negative_fields=result["negative_fields"], red_flags=result["red_flags"], ai_used=result["ai_used"])}


@router.post("/finalize", response_model=dict[str, InterviewFinalizeResponse])
async def finalize_interview(session_id: str, controller: InterviewController = Depends(get_interview_controller)) -> dict[str, InterviewFinalizeResponse]:
    try:
        result = await controller.finalize(session_id)
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if message ==
                            "Clinical session not found" else status.HTTP_400_BAD_REQUEST, detail=message) from exc
    return {"data": InterviewFinalizeResponse(session_id=result["session"].session_id, status=result["session"].status.value, summary=result["summary"].model_dump(mode="json"), triage=result["triage"].model_dump(mode="json"))}
