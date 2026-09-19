from datetime import datetime
from pydantic import BaseModel, Field
from backend.domain.enums import ConversationInputType


class ClinicalIntelligenceTurnRequest(BaseModel):
    draft_id: str = Field(min_length=1)
    local_id: str = Field(min_length=1)
    verification_token: str = Field(min_length=1)
    identity_method: str = Field(min_length=1)
    identity_identifier: str = Field(min_length=1)
    input_type: ConversationInputType
    content: str = Field(min_length=1)
    language: str = Field(
        min_length=2,
        max_length=16,
    )


class ClinicalIntelligenceTurnResponse(BaseModel):
    turn_id: str
    session_id: str
    speaker: str
    input_type: ConversationInputType
    content: str
    language: str | None
    created_at: datetime
    assistant_response: str | None
    next_question: str | None
    completed: bool
