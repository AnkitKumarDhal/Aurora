from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_clinical_session_service
from backend.api.schemas.sessions import CreateSessionRequest, SessionResponse
from backend.domain.clinical_session import ClinicalSession
from backend.services.clinical_session import ClinicalSessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_response(session: ClinicalSession) -> SessionResponse:
    return SessionResponse(
        session_id=session.session_id,
        patient_id=session.patient_id,
        department_id=session.department_id,
        status=session.status,
        verification_status=session.verification_status,
        consent_status=session.consent_status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    service: ClinicalSessionService = Depends(get_clinical_session_service),
) -> dict:
    now = ClinicalSession.model_fields["created_at"].default_factory()
    session = ClinicalSession(
        session_id=f"sess_{uuid4().hex}",
        patient_id="unverified",
        department_id=request.department_id,
        created_at=now,
        updated_at=now,
    )
    created_session = await service.create_session(session)
    return {"data": _to_response(created_session).model_dump(mode="json")}


@router.get("/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    service: ClinicalSessionService = Depends(get_clinical_session_service),
) -> dict:
    session = await service.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical session not found",
        )

    return {"data": _to_response(session).model_dump(mode="json")}


@router.post("/{session_id}/abandon", response_model=dict)
async def abandon_session(
    session_id: str,
    service: ClinicalSessionService = Depends(get_clinical_session_service),
) -> dict:
    try:
        session = await service.abandon_session(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical session not found",
        )

    return {"data": _to_response(session).model_dump(mode="json")}
