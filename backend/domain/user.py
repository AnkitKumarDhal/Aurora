from backend.domain.common import TimestampedModel
from backend.domain.enums import ActorRole


class User(TimestampedModel):
    user_id: str
    username: str
    password_hash: str
    role: ActorRole
    actor_id: str
    is_active: bool
