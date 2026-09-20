import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from backend.api.dependencies import (
    get_patient_intake_completion_service,
    get_patient_registration_service,
)
from backend.api.schemas.patient_registration import (
    PatientIntakeCompletionRequest,
    PatientIntakeCompletionResponse,
    PatientRegistrationDocument,
    PatientRegistrationDraft,
)
from backend.services.patient_intake_completion import (
    PatientIntakeCompletionService,
)
from backend.api.dependencies import get_patient_registration_service
from backend.api.schemas.patient_registration import (
    PatientRegistrationDocument,
    PatientRegistrationDraft,
)
from backend.services.patient_registration import PatientRegistrationService

router = APIRouter(
    prefix="/patient-intake",
    tags=["patient intake"],
)


@router.post(
    "/submit",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def submit_patient_registration(
    draft: str = Form(...),
    documents: str = Form("[]"),
    files: list[UploadFile] = File(default=[]),
    service: PatientRegistrationService = Depends(
        get_patient_registration_service,
    ),
) -> dict:
    try:
        draft_payload = PatientRegistrationDraft.model_validate(
            json.loads(draft),
        )

        document_payload = [
            PatientRegistrationDocument.model_validate(item)
            for item in json.loads(documents)
        ]

        if not draft_payload.consent_granted:
            raise ValueError(
                "Patient consent is required before final submission",
            )

        session, patient, visit_type = await service.submit(
            draft_id=draft_payload.draft_id,
            verification_token=draft_payload.verification_token,
            identity_method=draft_payload.identity_method,
            identity_identifier=draft_payload.identity_identifier,
            consent_version=draft_payload.consent_version,
            conversation_turns=[
                turn.model_dump()
                for turn in draft_payload.conversation_turns
            ],
            documents=[
                document.model_dump()
                for document in document_payload
            ],
            files=files,
            department_id="general-medicine",
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "data": {
            "session_id": session.session_id,
            "patient_id": patient.patient_id,
            "status": session.status.value,
            "visit_type": visit_type,
        },
    }


@router.post(
    "/complete",
    response_model=dict[str, PatientIntakeCompletionResponse],
)
async def complete_patient_intake(
    request: PatientIntakeCompletionRequest,
    service: PatientIntakeCompletionService = Depends(
        get_patient_intake_completion_service,
    ),
) -> dict[str, PatientIntakeCompletionResponse]:
    try:
        result = await service.complete(
            session_id=request.session_id,
            draft_id=request.draft_id,
            verification_token=request.verification_token,
            identity_method=request.identity_method,
            identity_identifier=request.identity_identifier,
        )
    except ValueError as exc:
        message = str(exc)

        response_status = (
            status.HTTP_404_NOT_FOUND
            if message == "Clinical session not found"
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    return {
        "data": PatientIntakeCompletionResponse(
            session_id=result["session_id"],
            status=result["status"],
            queue_entry_id=result["queue_entry_id"],
            doctor_id=result["doctor_id"],
        ),
    }
