from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_triage_service
from backend.api.schemas.triage import TriageAssessRequest, TriageResponse
from backend.services.triage import TriageService

router = APIRouter(
    prefix="/sessions/{session_id}/triage",
    tags=["triage"],
)


def _to_response(result) -> TriageResponse:
    return TriageResponse(
        triage_id=result.triage_id,
        session_id=result.session_id,
        status=result.status,
        urgency_level=result.urgency_level,
        priority_score=result.priority_score,
        red_flags_present=result.red_flags_present,
        assessed_at=result.assessed_at,
    )


@router.get(
    "",
    response_model=dict[str, TriageResponse],
)
async def get_triage(
    session_id: str,
    service=Depends(get_triage_service),
) -> dict[str, TriageResponse]:
    result = await service.get_session_result(session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Triage result not found",
        )

    return {"data": _to_response(result)}


@router.post(
    "",
    response_model=dict[str, TriageResponse],
)
async def assess_triage(
    session_id: str,
    request: TriageAssessRequest,
    service=Depends(get_triage_service),
) -> dict[str, TriageResponse]:
    signals = await service.get_session_signals(session_id)

    if signals is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical signals not found",
        )

    result = await service.get_session_result(session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Triage result not found",
        )

    assessed = await service.assess_from_signals(
        result.triage_id,
        signals,
    )

    if assessed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Triage result not found",
        )

    return {"data": _to_response(assessed)}
