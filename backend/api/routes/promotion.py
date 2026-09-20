from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from backend.api.dependencies import (
    get_promotion_service,
    get_promotion_workflow_service,
)
from backend.api.schemas.promotion import (
    PromotionCreateRequest,
    PromotionDecisionRequest,
    PromotionResponse,
)
from backend.auth.dependencies import (
    require_roles,
)
from backend.domain.enums import (
    ActorRole,
)
from backend.domain.promotion import (
    PromotionRequest,
)
from backend.domain.user import User
from backend.services.promotion import (
    PromotionService,
)
from backend.services.promotion_workflow import (
    PromotionWorkflowService,
)


router = APIRouter(
    prefix="/promotions",
    tags=["promotion"],
)


def _to_response(
    request: PromotionRequest,
) -> PromotionResponse:
    return PromotionResponse(
        promotion_request_id=(
            request.promotion_request_id
        ),
        queue_entry_id=(
            request.queue_entry_id
        ),
        target_doctor_id=(
            request.target_doctor_id
        ),
        reason=request.reason,
        status=request.status,
        decision_deadline=(
            request.decision_deadline
        ),
        decided_by=request.decided_by,
        decision_reason=(
            request.decision_reason
        ),
        decided_at=request.decided_at,
    )


@router.get(
    "/pending",
    response_model=dict[
        str,
        list[PromotionResponse],
    ],
)
async def get_pending_promotions(
    _: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    service: PromotionService = Depends(
        get_promotion_service,
    ),
) -> dict[
    str,
    list[PromotionResponse],
]:
    requests = (
        await service.get_pending_requests()
    )

    return {
        "data": [
            _to_response(request)
            for request in requests
        ],
    }


@router.get(
    "/{promotion_request_id}",
    response_model=dict[
        str,
        PromotionResponse,
    ],
)
async def get_promotion(
    promotion_request_id: str,
    _: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    service: PromotionService = Depends(
        get_promotion_service,
    ),
) -> dict[
    str,
    PromotionResponse,
]:
    request = await service.get_request(
        promotion_request_id,
    )

    if request is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Promotion request not found"
            ),
        )

    return {
        "data": _to_response(request),
    }


@router.post(
    "",
    response_model=dict[
        str,
        PromotionResponse,
    ],
)
async def create_promotion(
    request: PromotionCreateRequest,
    _: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    service: PromotionService = Depends(
        get_promotion_service,
    ),
    workflow: PromotionWorkflowService = Depends(
        get_promotion_workflow_service,
    ),
) -> dict[
    str,
    PromotionResponse,
]:
    try:
        result = (
            await workflow.create_manual_request(
                queue_entry_id=(
                    request.queue_entry_id
                ),
                target_doctor_id=(
                    request.target_doctor_id
                ),
                reason=request.reason,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(exc),
        ) from exc

    return {
        "data": _to_response(result),
    }


@router.post(
    "/{promotion_request_id}/approve",
    response_model=dict[
        str,
        PromotionResponse,
    ],
)
async def approve_promotion(
    promotion_request_id: str,
    request: PromotionDecisionRequest,
    current_user: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    workflow: PromotionWorkflowService = Depends(
        get_promotion_workflow_service,
    ),
) -> dict[
    str,
    PromotionResponse,
]:
    try:
        result = await workflow.approve(
            promotion_request_id,
            decided_by=current_user.actor_id,
            decision_reason=(
                request.decision_reason
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Promotion request not found"
            ),
        )

    return {
        "data": _to_response(result),
    }


@router.post(
    "/{promotion_request_id}/deny",
    response_model=dict[
        str,
        PromotionResponse,
    ],
)
async def deny_promotion(
    promotion_request_id: str,
    request: PromotionDecisionRequest,
    current_user: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    workflow: PromotionWorkflowService = Depends(
        get_promotion_workflow_service,
    ),
) -> dict[
    str,
    PromotionResponse,
]:
    try:
        result = await workflow.deny(
            promotion_request_id,
            decided_by=current_user.actor_id,
            decision_reason=(
                request.decision_reason
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Promotion request not found"
            ),
        )

    return {
        "data": _to_response(result),
    }


@router.post(
    "/{promotion_request_id}/cancel",
    response_model=dict[
        str,
        PromotionResponse,
    ],
)
async def cancel_promotion(
    promotion_request_id: str,
    request: PromotionDecisionRequest,
    current_user: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    workflow: PromotionWorkflowService = Depends(
        get_promotion_workflow_service,
    ),
) -> dict[
    str,
    PromotionResponse,
]:
    try:
        result = await workflow.cancel(
            promotion_request_id,
            request.decision_reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Promotion request not found"
            ),
        )

    return {
        "data": _to_response(result),
    }
