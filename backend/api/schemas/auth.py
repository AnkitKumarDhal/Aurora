from pydantic import BaseModel, Field
from backend.domain.enums import ActorRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    user_id: str
    username: str
    display_name: str | None = None
    role: ActorRole
    actor_id: str
