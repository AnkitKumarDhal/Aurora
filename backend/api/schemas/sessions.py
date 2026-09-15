from datetime import datetime
from pydantic import BaseModel, Field
from backend.domain.enums import ConsentStatus, SessionStatus, VerificationStatus


class CreateSessionRequest(BaseModel):
    department_id: str = Field(min_length=1)


class SessionResponse(BaseModel):
    session_id: str
    patient_id: str
    department_id: str
    status: SessionStatus
    verification_status: VerificationStatus
    consent_status: ConsentStatus
    created_at: datetime
    updated_at: datetime
