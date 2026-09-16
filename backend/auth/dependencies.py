from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.dependencies import get_authentication_service
from backend.auth.service import AuthenticationError, AuthenticationService
from backend.domain.enums import ActorRole
from backend.domain.user import User


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme,
    ),
    service: AuthenticationService = Depends(
        get_authentication_service,
    ),
) -> User:
    try:
        return service.decode_access_token(
            credentials.credentials,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc


def require_roles(
    *allowed_roles: ActorRole,
) -> Callable:
    async def dependency(
        current_user: User = Depends(
            get_current_user,
        ),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency
