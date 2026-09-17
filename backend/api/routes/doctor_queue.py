from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_doctor_queue_service
from backend.api.schemas.clinical_summary import ClinicalSummaryResponse
from backend.api.schemas.doctor_queue import (
    DoctorQueueEntryResponse,
    DoctorQueuePatientResponse,
    DoctorQueueResponse,
)
from backend.auth.dependencies import require_roles
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.services.doctor_queue import DoctorQueueService


router = APIRouter(
    prefix="/doctors/me/queue",
    tags=["doctor-queue"],
)


def _waiting_time_seconds(
    queued_at: datetime | None,
) -> int | None:
    if queued_at is None:
        return None

    if queued_at.tzinfo is None:
        queued_at = queued_at.replace(tzinfo=timezone.utc)
    else:
        queued_at = queued_at.astimezone(timezone.utc)

    now = datetime.now(timezone.utc)
    return max(0, int((now - queued_at).total_seconds()))


def _summary_response(summary) -> ClinicalSummaryResponse | None:
    if summary is None:
        return None

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
    response_model=dict[str, DoctorQueueResponse],
)
async def get_doctor_queue(
    current_user: User = Depends(
        require_roles(ActorRole.DOCTOR),
    ),
    service: DoctorQueueService = Depends(
        get_doctor_queue_service,
    ),
) -> dict[str, DoctorQueueResponse]:
    entries = await service.get_doctor_queue(
        current_user.actor_id,
    )

    response_entries = []

    for item in entries:
        entry = item["queue_entry"]
        patient = item["patient"]
        summary = item["summary"]

        response_entries.append(
            DoctorQueueEntryResponse(
                queue_entry_id=entry.queue_entry_id,
                session_id=entry.session_id,
                position=entry.position,
                urgency_level=entry.urgency_level,
                waiting_time_seconds=_waiting_time_seconds(
                    entry.queued_at,
                ),
                doctor_id=entry.doctor_id,
                status=entry.status,
                patient=(
                    DoctorQueuePatientResponse(
                        patient_id=patient.patient_id,
                        display_name=patient.display_name,
                        age=patient.age,
                    )
                    if patient is not None
                    else None
                ),
                summary=_summary_response(summary),
                queued_at=entry.queued_at,
                called_at=entry.called_at,
            ),
        )

    return {
        "data": DoctorQueueResponse(
            entries=response_entries,
        ),
    }
