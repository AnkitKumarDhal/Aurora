from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_verification_service
from backend.api.schemas.verification import (
    VerificationOtpRequest,
    VerificationOtpResponse,
    VerificationRequest,
    VerificationResponse,
)
from backend.domain.enums import VerificationStatus
from backend.services.verification import VerificationService

router = APIRouter(
    prefix="/sessions/{session_id}/verification",
    tags=["verification"],
)


@router.post(
    "/otp",
    response_model=dict[str, VerificationOtpResponse],
)
async def request_verification_otp(
    session_id: str,
    request: VerificationOtpRequest,
    service: VerificationService = Depends(get_verification_service),
) -> dict[str, VerificationOtpResponse]:
    try:
        challenge = await service.request_otp(
            session_id,
            request.method,
            request.identifier,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "data": VerificationOtpResponse(
            challenge_id=challenge.challenge_id,
            masked_destination=challenge.masked_destination,
            expires_in_seconds=challenge.expires_in_seconds,
            demo_otp=challenge.demo_otp,
        ),
    }


@router.post("", response_model=dict)
async def verify_patient(
    session_id: str,
    request: VerificationRequest,
    service: VerificationService = Depends(get_verification_service),
) -> dict:
    try:
        verification_id, result, existing_patient = (
            await service.verify_otp(
                session_id,
                request.challenge_id,
                request.otp,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    visit_type = (
        "RETURNING_VISIT"
        if existing_patient is not None
        else "FIRST_VISIT"
    )

    response = VerificationResponse(
        verification_id=verification_id,
        status=result.status,
        patient_id=(
            existing_patient.patient_id
            if existing_patient is not None
            else None
        ),
        existing_patient=existing_patient is not None,
        visit_type=visit_type,
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

    existing_patient = patient_id is not None

    response = VerificationResponse(
        verification_id=verification_id,
        status=verification_status,
        patient_id=patient_id,
        existing_patient=existing_patient,
        visit_type=(
            "RETURNING_VISIT"
            if existing_patient
            else "FIRST_VISIT"
        ),
    )

    return {"data": response.model_dump(mode="json")}
