from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from backend.config import settings
from backend.database.repositories.user import UserRepository
from backend.domain.enums import ActorRole
from backend.domain.user import User


class AuthenticationError(ValueError):
    pass


class AuthenticationService:
    def __init__(self, repository: UserRepository,) -> None:
        self.repository = repository
        self.password_hash = PasswordHash.recommended()

    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> User:
        document = await self.repository.get_by_username(username,)
        if document is None:
            raise AuthenticationError("Invalid username or password",)
        if not document.is_active:
            raise AuthenticationError("User account is inactive",)
        if not self.password_hash.verify(
            password,
            document.password_hash,
        ):
            raise AuthenticationError("Invalid username or password",)

        return User(
            user_id=document.user_id,
            username=document.username,
            password_hash=document.password_hash,
            role=document.role,
            actor_id=document.actor_id,
            is_active=document.is_active,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def create_access_token(
        self,
        user: User,
    ) -> str:
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + \
            timedelta(minutes=settings.jwt_access_token_minutes,)
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "actor_id": user.actor_id,
            "iat": issued_at,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

    def decode_access_token(
        self,
        token: str,
    ) -> User:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Invalid access token") from exc

        user_id = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")
        actor_id = payload.get("actor_id")

        if not all([
            user_id,
            username,
            role,
            actor_id,
        ]):
            raise AuthenticationError("Invalid access token payload")

        try:
            actor_role = ActorRole(role)
        except ValueError as exc:
            raise AuthenticationError("Invalid access token role") from exc

        return User(
            user_id=user_id,
            username=username,
            password_hash="",
            role=actor_role,
            actor_id=actor_id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
