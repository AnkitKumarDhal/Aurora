from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import (
    get_authentication_service,
    get_doctor_repository,
)
from backend.api.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
)
from backend.auth.dependencies import get_current_user
from backend.auth.service import (
    AuthenticationError,
    AuthenticationService,
)
from backend.domain.enums import ActorRole
from backend.domain.user import User
from backend.database.repositories.doctor import DoctorRepository


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/login",
    response_model=dict[str, LoginResponse],
)
async def login(
    request: LoginRequest,
    service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> dict[str, LoginResponse]:
    try:
        user = await service.authenticate(
            request.username,
            request.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    return {
        "data": LoginResponse(
            access_token=service.create_access_token(
                user,
            ),
        ),
    }


@router.get(
    "/me",
    response_model=dict[str, CurrentUserResponse],
)
async def get_current_user_info(
    current_user: User = Depends(
        get_current_user,
    ),
    doctor_repository: DoctorRepository = Depends(
        get_doctor_repository,
    ),
) -> dict[str, CurrentUserResponse]:
    display_name = None

    if current_user.role == ActorRole.DOCTOR:
        doctor = await doctor_repository.get_doctor(
            current_user.actor_id,
        )

        if doctor is not None:
            display_name = doctor.display_name

    return {
        "data": CurrentUserResponse(
            user_id=current_user.user_id,
            username=current_user.username,
            display_name=display_name,
            role=current_user.role,
            actor_id=current_user.actor_id,
        ),
    }
