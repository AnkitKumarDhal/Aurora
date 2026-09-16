from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_workflow_service
from backend.api.schemas.queue import QueueEntryResponse
from backend.api.schemas.workflow import AssignmentResponse, WorkflowAssignmentResponse, WorkflowQueueActionResponse
from backend.services.workflow import WorkflowService

router = APIRouter(
    prefix="/sessions",
    tags=["workflow"],
)


def _queue_response(entry) -> QueueEntryResponse:
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


def _assignment_response(assignment) -> AssignmentResponse:
    return AssignmentResponse(
        assignment_id=assignment.assignment_id,
        session_id=assignment.session_id,
        doctor_id=assignment.doctor_id,
        department_id=assignment.department_id,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        released_at=assignment.released_at,
    )


@router.post(
    "/{session_id}/queue",
    response_model=dict[str, WorkflowQueueActionResponse],
)
async def queue_session(
    session_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, WorkflowQueueActionResponse]:
    try:
        entry = await service.queue_session_from_triage(session_id)
    except ValueError as exc:
        message = str(exc)
        response_status = (
            status.HTTP_404_NOT_FOUND
            if message in {
                "Clinical session not found",
                "Triage result not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    return {
        "data": WorkflowQueueActionResponse(
            queue_entry=_queue_response(entry),
        ),
    }


@router.post(
    "/{session_id}/queue/{queue_entry_id}/assign",
    response_model=dict[str, WorkflowAssignmentResponse],
)
async def assign_patient(
    session_id: str,
    queue_entry_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, WorkflowAssignmentResponse]:
    try:
        assignment = await service.assign_patient(
            session_id,
            queue_entry_id,
        )
    except ValueError as exc:
        message = str(exc)
        response_status = (
            status.HTTP_404_NOT_FOUND
            if message in {
                "Clinical session not found",
                "Queue entry not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No available doctor for assignment",
        )

    return {
        "data": WorkflowAssignmentResponse(
            assignment=_assignment_response(assignment),
        ),
    }


@router.post(
    "/{session_id}/queue/{queue_entry_id}/call",
    response_model=dict[str, WorkflowQueueActionResponse],
)
async def call_patient(
    session_id: str,
    queue_entry_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, WorkflowQueueActionResponse]:
    try:
        entry = await service.call_patient(
            session_id,
            queue_entry_id,
        )
    except ValueError as exc:
        message = str(exc)
        response_status = (
            status.HTTP_404_NOT_FOUND
            if message in {
                "Clinical session not found",
                "Queue entry not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    return {
        "data": WorkflowQueueActionResponse(
            queue_entry=_queue_response(entry),
        ),
    }


@router.post(
    "/{session_id}/queue/{queue_entry_id}/start-consultation",
    response_model=dict[str, WorkflowQueueActionResponse],
)
async def start_consultation(
    session_id: str,
    queue_entry_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, WorkflowQueueActionResponse]:
    try:
        entry = await service.start_consultation(
            session_id,
            queue_entry_id,
        )
    except ValueError as exc:
        message = str(exc)
        response_status = (
            status.HTTP_404_NOT_FOUND
            if message in {
                "Clinical session not found",
                "Queue entry not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    return {
        "data": WorkflowQueueActionResponse(
            queue_entry=_queue_response(entry),
        ),
    }


@router.post(
    "/{session_id}/queue/{queue_entry_id}/complete",
    response_model=dict[str, WorkflowQueueActionResponse],
)
async def complete_consultation(
    session_id: str,
    queue_entry_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, WorkflowQueueActionResponse]:
    try:
        entry = await service.complete_consultation(
            session_id,
            queue_entry_id,
        )
    except ValueError as exc:
        message = str(exc)
        response_status = (
            status.HTTP_404_NOT_FOUND
            if message in {
                "Clinical session not found",
                "Queue entry not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    return {
        "data": WorkflowQueueActionResponse(
            queue_entry=_queue_response(entry),
        ),
    }
