from fastapi import APIRouter, Depends

from backend.api.dependencies import get_admin_dashboard_service
from backend.api.schemas.admin_dashboard import (
    AdminDashboardResponse,
)
from backend.auth.dependencies import require_roles
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.services.admin_dashboard import AdminDashboardService


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get(
    "/departments/{department_id}/dashboard",
    response_model=dict[str, AdminDashboardResponse],
)
async def get_admin_dashboard(
    department_id: str,
    current_user: User = Depends(
        require_roles(ActorRole.ADMIN),
    ),
    service: AdminDashboardService = Depends(
        get_admin_dashboard_service,
    ),
) -> dict[str, AdminDashboardResponse]:
    dashboard = await service.get_dashboard(
        department_id,
    )

    return {
        "data": AdminDashboardResponse.model_validate(
            dashboard,
        ),
    }
