from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_patient_session_service
from backend.api.schemas.patient_session import (
    PreparePatientSessionRequest,
    PreparePatientSessionResponse,
)
from backend.services.patient_session import PatientSessionPreparationService


router = APIRouter(
    prefix="/patient-intake/session",
    tags=["patient intake"],
)


@router.post(
    "/prepare",
    response_model=dict[str, PreparePatientSessionResponse],
    status_code=status.HTTP_200_OK,
)
async def prepare_patient_session(
    request: PreparePatientSessionRequest,
    service: PatientSessionPreparationService = Depends(
        get_patient_session_service,
    ),
) -> dict[str, PreparePatientSessionResponse]:
    try:
        session = await service.prepare(
            draft_id=request.draft_id,
            verification_token=request.verification_token,
            identity_method=request.identity_method,
            identity_identifier=request.identity_identifier,
            consent_version=request.consent_version,
            department_id=request.department_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "data": PreparePatientSessionResponse(
            session_id=session.session_id,
            status=session.status,
            verification_status=session.verification_status,
            consent_status=session.consent_status,
        ),
    }
