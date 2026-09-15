from datetime import datetime
from pydantic import BaseModel, Field
from backend.domain.enums import ConversationInputType


class ConversationTurnRequest(BaseModel):
    input_type: ConversationInputType
    content: str | None = None
    language: str | None = Field(default=None, min_length=2, max_length=10)
    media_reference: str | None = None


class ConversationTurnResponse(BaseModel):
    turn_id: str
    speaker: str
    input_type: ConversationInputType
    content: str | None
    language: str | None
    media_reference: str | None
    created_at: datetime
