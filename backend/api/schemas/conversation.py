from datetime import datetime
from pydantic import BaseModel, Field
from backend.domain.enums import ConversationInputType


class ConversationTurnRequest(BaseModel):
    input_type: ConversationInputType
    content: str | None = None
    language: str | None = Field(default=None, min_length=2, max_length=16)
    media_reference: str | None = None


class ConversationTurnResponse(BaseModel):
    turn_id: str
    session_id: str
    speaker: str
    input_type: ConversationInputType
    content: str | None = None
    language: str | None = None
    media_reference: str | None = None
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    turns: list[ConversationTurnResponse]
