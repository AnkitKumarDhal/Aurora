from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_ephemeral_identity_service
from backend.api.schemas.patient_verification import (
    PatientVerificationOtpRequest,
    PatientVerificationOtpResponse,
    PatientVerificationOtpVerifyRequest,
    PatientVerificationOtpVerifyResponse,
)
from backend.integrations.identity import IdentityProviderUnavailableError
from backend.services.ephemeral_identity import EphemeralIdentityService

router = APIRouter(prefix="/identity", tags=["patient identity"])


@router.post("/otp", response_model=dict[str, PatientVerificationOtpResponse])
async def request_patient_verification_otp(
    request: PatientVerificationOtpRequest,
    service: EphemeralIdentityService = Depends(
        get_ephemeral_identity_service,
    ),
) -> dict[str, PatientVerificationOtpResponse]:
    try:
        challenge = await service.request_otp(
            request.draft_id,
            request.method,
            request.identifier,
        )
    except IdentityProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "data": PatientVerificationOtpResponse(
            challenge_id=challenge.challenge_id,
            masked_destination=challenge.masked_destination,
            expires_in_seconds=challenge.expires_in_seconds,
            demo_otp=challenge.demo_otp,
        ),
    }


@router.post(
    "/otp/verify",
    response_model=dict[str, PatientVerificationOtpVerifyResponse],
)
async def verify_patient_verification_otp(
    request: PatientVerificationOtpVerifyRequest,
    service: EphemeralIdentityService = Depends(
        get_ephemeral_identity_service,
    ),
) -> dict[str, PatientVerificationOtpVerifyResponse]:
    try:
        verification = await service.verify_otp(
            request.draft_id,
            request.challenge_id,
            request.otp,
        )
    except IdentityProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "data": PatientVerificationOtpVerifyResponse(
            verification_token=verification.token,
            status=verification.result.status.value,
            expires_in_seconds=service.VERIFICATION_TTL_SECONDS,
        ),
    }
