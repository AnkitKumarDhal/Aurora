from fastapi import APIRouter, Depends, HTTPException, status
from backend.auth.dependencies import require_roles
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.api.dependencies import get_promotion_service
from backend.api.schemas.promotion import PromotionCreateRequest, PromotionDecisionRequest, PromotionResponse
from backend.domain.promotion import PromotionRequest
from backend.services.promotion import PromotionService


router = APIRouter(
    prefix="/promotions",
    tags=["promotion"],
)


def _to_response(
    request: PromotionRequest,
) -> PromotionResponse:
    return PromotionResponse(
        promotion_request_id=request.promotion_request_id,
        queue_entry_id=request.queue_entry_id,
        reason=request.reason,
        status=request.status,
        decision_deadline=request.decision_deadline,
        decided_by=request.decided_by,
        decision_reason=request.decision_reason,
        decided_at=request.decided_at,
    )


@router.get(
    "/pending",
    response_model=dict[str, list[PromotionResponse]],
)
async def get_pending_promotions(
    service: PromotionService = Depends(
        get_promotion_service
    ),
) -> dict[str, list[PromotionResponse]]:
    requests = await service.get_pending_requests()

    return {
        "data": [
            _to_response(request)
            for request in requests
        ],
    }


@router.get(
    "/{promotion_request_id}",
    response_model=dict[str, PromotionResponse],
)
async def get_promotion(
    promotion_request_id: str,
    service: PromotionService = Depends(
        get_promotion_service
    ),
) -> dict[str, PromotionResponse]:
    request = await service.get_request(
        promotion_request_id,
    )

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion request not found",
        )

    return {
        "data": _to_response(request),
    }


@router.post(
    "",
    response_model=dict[str, PromotionResponse],
)
async def create_promotion(
    request: PromotionCreateRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
) -> dict[str, PromotionResponse]:
    try:
        result = await service.create_promotion_request(
            request.queue_entry_id,
            request.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return {
        "data": _to_response(result),
    }


@router.post(
    "/{promotion_request_id}/approve",
    response_model=dict[str, PromotionResponse],
)
async def approve_promotion(
    promotion_request_id: str,
    request: PromotionDecisionRequest,
    current_user: User = Depends(
        require_roles(ActorRole.ADMIN)
    ),
    service: PromotionService = Depends(
        get_promotion_service
    ),
) -> dict[str, PromotionResponse]:
    result = await service.approve(
        promotion_request_id,
        decided_by=current_user.actor_id,
        decision_reason=request.decision_reason,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion request not found",
        )

    return {
        "data": _to_response(result),
    }


@router.post(
    "/{promotion_request_id}/deny",
    response_model=dict[str, PromotionResponse],
)
async def deny_promotion(
    promotion_request_id: str,
    request: PromotionDecisionRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
) -> dict[str, PromotionResponse]:
    result = await service.deny(
        promotion_request_id,
        decided_by="admin",
        decision_reason=request.decision_reason,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion request not found",
        )

    return {
        "data": _to_response(result),
    }


@router.post(
    "/{promotion_request_id}/cancel",
    response_model=dict[str, PromotionResponse],
)
async def cancel_promotion(
    promotion_request_id: str,
    request: PromotionDecisionRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
) -> dict[str, PromotionResponse]:
    result = await service.cancel(
        promotion_request_id,
        request.decision_reason,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion request not found",
        )

    return {
        "data": _to_response(result),
    }
