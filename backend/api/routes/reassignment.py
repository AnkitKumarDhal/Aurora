from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from backend.api.dependencies import (
    get_reassignment_service,
)
from backend.api.schemas.reassignment import (
    ReassignmentRequest,
    ReassignmentResponse,
)
from backend.auth.dependencies import require_roles
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.services.reassignment import (
    ReassignmentService,
)


router = APIRouter(
    prefix="/admin/reassignments",
    tags=["admin-reassignment"],
)


@router.post(
    "",
    response_model=dict[str, ReassignmentResponse],
)
async def reassign_patient(
    request: ReassignmentRequest,
    current_user: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    service: ReassignmentService = Depends(
        get_reassignment_service,
    ),
) -> dict[str, ReassignmentResponse]:
    try:
        result = await service.reassign(
            request.queue_entry_id,
            request.doctor_id,
        )
    except ValueError as exc:
        message = str(exc)

        response_status = (
            status.HTTP_404_NOT_FOUND
            if message
            in {
                "Queue entry not found",
                "Target doctor not found",
                "Active doctor assignment not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc

    return {
        "data": ReassignmentResponse(
            queue_entry_id=result.queue_entry_id,
            session_id=result.session_id,
            previous_doctor_id=(
                result.previous_doctor_id
            ),
            doctor_id=result.doctor_id,
            assignment_id=result.assignment_id,
        ),
    }
