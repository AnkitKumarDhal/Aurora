from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_clinical_summary_service
from backend.api.schemas.clinical_summary import ClinicalSummaryCreateRequest, ClinicalSummaryResponse, ClinicalSummaryUpdateRequest
from backend.auth.authorization import require_assigned_doctor_access
from backend.domain.clinical_summary import ClinicalSummary
from backend.domain.user import User
from backend.services.clinical_summary import ClinicalSummaryService

router = APIRouter(
    prefix="/sessions/{session_id}/summary",
    tags=["clinical-summary"],
)


def _to_response(summary: ClinicalSummary) -> ClinicalSummaryResponse:
    return ClinicalSummaryResponse(
        summary_id=summary.summary_id,
        session_id=summary.session_id,
        status=summary.status,
        chief_complaint=summary.chief_complaint,
        history_of_present_illness=summary.history_of_present_illness,
        past_medical_history=summary.past_medical_history,
        medications=summary.medications,
        allergies=summary.allergies,
        relevant_documents=summary.relevant_documents,
        clinical_signals=summary.clinical_signals,
        generated_at=summary.generated_at,
        confirmed_by=summary.confirmed_by,
        confirmed_at=summary.confirmed_at,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


@router.get(
    "",
    response_model=dict[str, ClinicalSummaryResponse],
)
async def get_summary(
    session_id: str,
    current_user: User = Depends(require_assigned_doctor_access),
    service: ClinicalSummaryService = Depends(get_clinical_summary_service),
) -> dict[str, ClinicalSummaryResponse]:
    summary = await service.get_session_summary(session_id)

    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Clinical summary not found")

    return {"data": _to_response(summary)}


@router.post(
    "",
    response_model=dict[str, ClinicalSummaryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_summary(
    session_id: str,
    request: ClinicalSummaryCreateRequest,
    current_user: User = Depends(require_assigned_doctor_access),
    service: ClinicalSummaryService = Depends(get_clinical_summary_service),
) -> dict[str, ClinicalSummaryResponse]:
    existing = await service.get_session_summary(session_id)

    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Clinical summary already exists")

    summary = ClinicalSummary(
        summary_id=f"summary_{uuid4().hex}",
        session_id=session_id,
        chief_complaint=request.chief_complaint,
        history_of_present_illness=request.history_of_present_illness,
        past_medical_history=request.past_medical_history,
        medications=request.medications,
        allergies=request.allergies,
        relevant_documents=request.relevant_documents,
        clinical_signals=request.clinical_signals,
        generated_at=request.generated_at,
    )

    try:
        result = await service.create_summary(summary)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"data": _to_response(result)}


@router.patch(
    "",
    response_model=dict[str, ClinicalSummaryResponse],
)
async def update_summary(
    session_id: str,
    request: ClinicalSummaryUpdateRequest,
    current_user: User = Depends(require_assigned_doctor_access),
    service: ClinicalSummaryService = Depends(get_clinical_summary_service),
) -> dict[str, ClinicalSummaryResponse]:
    summary = await service.get_session_summary(session_id)

    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Clinical summary not found")

    updates = request.model_dump(exclude_unset=True)

    try:
        result = await service.update_summary(summary.summary_id, updates)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Clinical summary not found")

    return {"data": _to_response(result)}


@router.post(
    "/confirm",
    response_model=dict[str, ClinicalSummaryResponse],
)
async def confirm_summary(
    session_id: str,
    current_user: User = Depends(require_assigned_doctor_access),
    service: ClinicalSummaryService = Depends(get_clinical_summary_service),
) -> dict[str, ClinicalSummaryResponse]:
    try:
        result = await service.confirm_summary(session_id, current_user.actor_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Clinical summary not found")

    return {"data": _to_response(result)}
