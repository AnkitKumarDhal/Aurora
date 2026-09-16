from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_intake_service
from backend.api.schemas.intake import IntakeFinalizeResponse
from backend.services.intake import IntakeService

router = APIRouter(prefix="/sessions", tags=["intake"])


@router.post("/{session_id}/finalize", response_model=dict[str, IntakeFinalizeResponse])
async def finalize_intake(session_id: str, service: IntakeService = Depends(get_intake_service)) -> dict[str, IntakeFinalizeResponse]:
    try:
        session = await service.finalize(session_id)
    except ValueError as exc:
        message = str(exc)
        response_status = (
            status.HTTP_404_NOT_FOUND
            if message in {
                "Clinical session not found",
                "Clinical summary not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical session not found",
        )

    return {
        "data": IntakeFinalizeResponse(
            session_id=session.session_id,
            status=session.status,
            updated_at=session.updated_at,
        ),
    }
