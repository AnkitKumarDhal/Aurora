from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_queue_service
from backend.api.schemas.queue import QueueEntryResponse
from backend.domain.queue import QueueEntry
from backend.services.queue import QueueService

router = APIRouter(
    prefix="/queue",
    tags=["queue"],
)


def _to_response(entry: QueueEntry) -> QueueEntryResponse:
    return QueueEntryResponse(
        queue_entry_id=entry.queue_entry_id,
        session_id=entry.session_id,
        department_id=entry.department_id,
        status=entry.status,
        position=entry.position,
        urgency_level=entry.urgency_level,
        priority_score=entry.priority_score,
        doctor_id=entry.doctor_id,
        queued_at=entry.queued_at,
        called_at=entry.called_at,
        completed_at=entry.completed_at,
    )


@router.get(
    "/departments/{department_id}",
    response_model=dict[str, list[QueueEntryResponse]],
)
async def get_department_queue(
    department_id: str,
    service: QueueService = Depends(get_queue_service),
) -> dict[str, list[QueueEntryResponse]]:
    entries = await service.get_department_queue(department_id)

    return {
        "data": [_to_response(entry) for entry in entries],
    }


@router.get(
    "/{queue_entry_id}",
    response_model=dict[str, QueueEntryResponse],
)
async def get_queue_entry(
    queue_entry_id: str,
    service: QueueService = Depends(get_queue_service),
) -> dict[str, QueueEntryResponse]:
    entry = await service.get_entry(queue_entry_id)

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue entry not found",
        )

    return {"data": _to_response(entry)}
