from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_consent_service
from backend.api.schemas.consent import ConsentRequest, ConsentResponse
from backend.domain.enums import ConsentStatus
from backend.services.consent import ConsentService

router = APIRouter(
    prefix="/sessions/{session_id}/consent",
    tags=["consent"],
)


@router.get("", response_model=dict)
async def get_consent(
    session_id: str,
    service: ConsentService = Depends(get_consent_service),
) -> dict:
    try:
        consent_status = await service.get_status(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return {
        "data": {
            "consent_status": consent_status.value,
        },
    }


@router.post("", response_model=dict)
async def record_consent(
    session_id: str,
    request: ConsentRequest,
    service: ConsentService = Depends(get_consent_service),
) -> dict:
    try:
        session_status = (
            await service.grant(session_id)
            if request.granted
            else await service.deny(session_id)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    consent_status = (
        ConsentStatus.GRANTED
        if request.granted
        else ConsentStatus.DENIED
    )

    response = ConsentResponse(
        consent_status=consent_status,
        recorded_at=datetime.now(timezone.utc),
    )

    return {
        "data": response.model_dump(mode="json"),
        "meta": {
            "session_status": session_status.value,
        },
    }
