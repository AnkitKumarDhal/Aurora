from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_verification_service
from backend.api.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
)
from backend.domain.enums import VerificationStatus
from backend.services.verification import VerificationService

router = APIRouter(
    prefix="/sessions/{session_id}/verification",
    tags=["verification"],
)


@router.post("", response_model=dict)
async def verify_patient(
    session_id: str,
    request: VerificationRequest,
    service: VerificationService = Depends(get_verification_service),
) -> dict:
    try:
        verification_id, result = await service.verify(
            session_id,
            request.method,
            request.identifier,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    response = VerificationResponse(
        verification_id=verification_id,
        status=result.status,
        patient_id=result.patient_id,
    )

    return {"data": response.model_dump(mode="json")}


@router.get("", response_model=dict)
async def get_verification(
    session_id: str,
    service: VerificationService = Depends(get_verification_service),
) -> dict:
    try:
        verification_id, verification_status, patient_id = (
            await service.get_status(session_id)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    response = VerificationResponse(
        verification_id=verification_id,
        status=verification_status,
        patient_id=patient_id,
    )

    return {"data": response.model_dump(mode="json")}
