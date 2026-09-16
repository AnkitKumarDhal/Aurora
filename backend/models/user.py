from datetime import datetime
from typing import ClassVar
from pydantic import Field
from backend.domain.enums import ActorRole
from .common import PersistenceModel


class UserDocument(PersistenceModel):
    user_id: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password_hash: str = Field(min_length=1)
    role: ActorRole
    actor_id: str = Field(min_length=1)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "users"
