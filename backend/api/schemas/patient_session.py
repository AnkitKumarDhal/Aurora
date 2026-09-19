from typing import Literal

from pydantic import BaseModel, Field
from backend.domain.enums import ConsentStatus, SessionStatus, VerificationStatus


class PreparePatientSessionRequest(BaseModel):
    draft_id: str = Field(min_length=1)
    verification_token: str = Field(min_length=1)
    identity_method: Literal["ABHA", "AADHAAR"]
    identity_identifier: str = Field(min_length=1)
    consent_version: str = Field(min_length=1)
    department_id: str = Field(
        default="general-medicine",
        min_length=1,
    )


class PreparePatientSessionResponse(BaseModel):
    session_id: str
    status: SessionStatus
    verification_status: VerificationStatus
    consent_status: ConsentStatus
