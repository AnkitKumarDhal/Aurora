import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

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
            detail="Unable to complete patient registration",
        ) from exc

    return {
        "data": {
            "session_id": session.session_id,
            "patient_id": patient.patient_id,
            "status": session.status.value,
            "visit_type": visit_type,
        },
    }
