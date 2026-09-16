from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_consent_service
from backend.api.schemas.consent import (
    ConsentInformationResponse,
    ConsentRequest,
    ConsentResponse,
)
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

    information = service.get_information()

    response = ConsentInformationResponse(
        version=information["version"],
        status=consent_status,
        text=information["text"],
        audio_available=information["audio_available"],
        supported_languages=information["supported_languages"],
    )

    return {
        "data": response.model_dump(mode="json"),
    }


@router.post("", response_model=dict)
async def record_consent(
    session_id: str,
    request: ConsentRequest,
    service: ConsentService = Depends(get_consent_service),
) -> dict:
    try:
        session_status = (
            await service.grant(session_id, request.version)
            if request.granted
            else await service.deny(session_id, request.version)
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
        version=request.version,
        consent_status=consent_status,
        recorded_at=datetime.now(timezone.utc),
    )

    return {
        "data": response.model_dump(mode="json"),
        "meta": {
            "session_status": session_status.value,
        },
    }
