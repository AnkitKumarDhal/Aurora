from datetime import datetime
from pydantic import Field
from .common import TimestampedModel
from .enums import ConversationInputType, Speaker


class ConversationTurn(TimestampedModel):
    turn_id: str
    session_id: str
    speaker: Speaker
    input_type: ConversationInputType
    content: str | None = None
    language: str | None = None
    media_reference: str | None = None
    created_at: datetime = Field(
        default_factor=lambda: datetime.now().astimezone())
