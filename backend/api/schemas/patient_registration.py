from typing import Literal

from pydantic import BaseModel, Field


class PatientRegistrationConversationTurn(BaseModel):
    local_id: str = Field(min_length=1)
    input_type: Literal["AUDIO", "GUIDED_INPUT", "TEXT"]
    content: str = Field(min_length=1)
    language: str = Field(min_length=1)


class PatientRegistrationDocument(BaseModel):
    local_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    document_type: Literal[
        "IMAGING_REPORT",
        "LAB_REPORT",
        "MEDICAL_RECORD",
        "OTHER",
        "PRESCRIPTION",
    ]


class PatientRegistrationDraft(BaseModel):
    version: Literal[1]
    draft_id: str = Field(min_length=1)
    language: Literal["en", "hi"]
    identity_method: Literal["ABHA", "AADHAAR"]
    identity_identifier: str = Field(min_length=1)
    verification_token: str = Field(min_length=1)
    consent_version: str = Field(min_length=1)
    consent_granted: bool
    conversation_turns: list[PatientRegistrationConversationTurn] = Field(
        default_factory=list,
    )
