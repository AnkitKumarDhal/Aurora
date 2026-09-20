from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_clinical_intelligence_service
from backend.api.schemas.clinical_intelligence import ClinicalIntelligenceResponse
from backend.auth.authorization import require_doctor_case_access
from backend.domain.user import User
from backend.services.clinical_intelligence import ClinicalIntelligenceService


router = APIRouter(
    prefix="/sessions/{session_id}/clinical-intelligence",
    tags=["clinical intelligence"],
)


@router.get(
    "",
    response_model=dict[str, ClinicalIntelligenceResponse],
)
async def get_clinical_intelligence(
    session_id: str,
    current_user: User = Depends(require_doctor_case_access),
    service: ClinicalIntelligenceService = Depends(
        get_clinical_intelligence_service,
    ),
) -> dict[str, ClinicalIntelligenceResponse]:
    result = await service.build(session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical session not found",
        )

    return {
        "data": ClinicalIntelligenceResponse(
            **result,
        ),
    }
