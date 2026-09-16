from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_assignment_repository
from backend.api.schemas.workflow import AssignmentResponse
from backend.auth.authorization import require_assigned_doctor_access
from backend.domain.user import User
from backend.services.assignment import AssignmentService


router = APIRouter(
    prefix="/sessions/{session_id}/assignment",
    tags=["assignment"],
)


def _to_response(assignment) -> AssignmentResponse:
    return AssignmentResponse(
        assignment_id=assignment.assignment_id,
        session_id=assignment.session_id,
        doctor_id=assignment.doctor_id,
        department_id=assignment.department_id,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        released_at=assignment.released_at,
    )


@router.get(
    "",
    response_model=dict[str, AssignmentResponse],
)
async def get_assignment(
    session_id: str,
    current_user: User = Depends(require_assigned_doctor_access),
    assignment_repository=Depends(get_assignment_repository),
) -> dict[str, AssignmentResponse]:
    service = AssignmentService(assignment_repository)

    assignment = await service.get_session_assignment(session_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    return {
        "data": _to_response(assignment),
    }
