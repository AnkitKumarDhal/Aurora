from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import (
    get_clinical_intelligence_service,
    get_patient_session_service,
)
from backend.api.schemas.clinical_intelligence import (
    ClinicalIntelligenceTurnRequest,
    ClinicalIntelligenceTurnResponse,
)
from backend.domain.conversation import ConversationTurn
from backend.domain.enums import Speaker
from backend.services.clinical_intelligence import (
    ClinicalIntelligenceService,
)
from backend.services.patient_session import (
    PatientSessionPreparationService,
)


router = APIRouter(
    prefix="/sessions/{session_id}/clinical-intelligence",
    tags=["clinical intelligence"],
)


@router.post(
    "/turns",
    response_model=dict[str, ClinicalIntelligenceTurnResponse],
    status_code=status.HTTP_201_CREATED,
)
async def process_clinical_intelligence_turn(
    session_id: str,
    request: ClinicalIntelligenceTurnRequest,
    patient_session_service: PatientSessionPreparationService = Depends(
        get_patient_session_service,
    ),
    service: ClinicalIntelligenceService = Depends(
        get_clinical_intelligence_service,
    ),
) -> dict[str, ClinicalIntelligenceTurnResponse]:
    try:
        await patient_session_service.validate_access(
            session_id=session_id,
            draft_id=request.draft_id,
            verification_token=request.verification_token,
            identity_method=request.identity_method,
            identity_identifier=request.identity_identifier,
        )

        turn = ConversationTurn(
            turn_id=patient_session_service.turn_id_for_draft(
                request.draft_id,
                request.local_id,
            ),
            session_id=session_id,
            speaker=Speaker.PATIENT,
            input_type=request.input_type,
            content=request.content,
            language=request.language,
            media_reference=None,
        )

        result = await service.process_turn(
            turn,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    stored_turn = result["turn"]

    return {
        "data": ClinicalIntelligenceTurnResponse(
            turn_id=stored_turn.turn_id,
            session_id=stored_turn.session_id,
            speaker=stored_turn.speaker.value.lower(),
            input_type=stored_turn.input_type,
            content=stored_turn.content or "",
            language=stored_turn.language,
            created_at=stored_turn.created_at,
            assistant_response=result.get(
                "assistant_response",
            ),
            next_question=result.get(
                "next_question",
            ),
            completed=bool(
                result.get(
                    "completed",
                    False,
                )
            ),
            question_field=result.get(
                "question_field",
            ),
            question_source=result.get(
                "question_source",
            ),
            question_reason=result.get(
                "question_reason",
            ),
            answer_mode=result.get(
                "answer_mode",
            ),
        ),
    }
