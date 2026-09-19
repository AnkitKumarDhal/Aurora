from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.domain.enums import ConversationInputType


class InterviewTurnRequest(BaseModel):
    draft_id: str = Field(min_length=1)
    client_turn_id: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=4000)
    input_type: ConversationInputType = ConversationInputType.TEXT
    language: str | None = Field(default=None, min_length=2, max_length=16)


class InterviewStateResponse(BaseModel):
    session_id: str
    topic: str
    known_fields: dict[str, Any]
    patient_turns: int
    next_question: str | None
    completed: bool
    red_flags: list[str]
    ai_enabled: bool


class InterviewTurnResponse(BaseModel):
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
    topic: str
    known_fields: dict[str, Any]
    extracted_fields: dict[str, Any]
    negative_fields: list[str]
    red_flags: list[str]
    ai_used: bool


class InterviewFinalizeResponse(BaseModel):
    session_id: str
    status: str
    summary: dict[str, Any]
    triage: dict[str, Any]
