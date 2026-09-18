from pydantic import BaseModel, Field

from backend.domain.enums import VerificationStatus


class VerificationRequest(BaseModel):
    method: str = Field(min_length=1)
    identifier: str = Field(min_length=1)


class VerificationResponse(BaseModel):
    verification_id: str
    status: VerificationStatus
    patient_id: str | None = None
    existing_patient: bool = False
    visit_type: str
