from datetime import datetime
from typing import ClassVar
from pydantic import Field
from domain.enums import ConversationInputType, Speaker
from .common import PersistenceModel


class ConversationTurnDocument(PersistenceModel):
    turn_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    speaker: Speaker
    input_type: ConversationInputType
    content: str | None = None
    language: str | None = None
    media_reference: str | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "conversation_turns"
