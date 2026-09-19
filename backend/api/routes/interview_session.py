from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_interview_session_service
from backend.api.schemas.interview_session import (
    PrepareInterviewSessionRequest,
    PrepareInterviewSessionResponse,
)
from backend.services.interview_session import InterviewSessionPreparationService


router = APIRouter(
    prefix="/patient-intake/interview",
    tags=["patient interview"],
)


@router.post(
    "/session",
    response_model=dict[str, PrepareInterviewSessionResponse],
)
async def prepare_interview_session(
    request: PrepareInterviewSessionRequest,
    service: InterviewSessionPreparationService = Depends(
        get_interview_session_service,
    ),
) -> dict[str, PrepareInterviewSessionResponse]:
    try:
        session = await service.prepare(
            draft_id=request.draft_id,
            verification_token=request.verification_token,
            identity_method=request.identity_method,
            identity_identifier=request.identity_identifier,
            department_id=request.department_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "data": PrepareInterviewSessionResponse(
            session_id=session.session_id,
            status=session.status,
            verification_status=session.verification_status,
            consent_status=session.consent_status,
        ),
    }
