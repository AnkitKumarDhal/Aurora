from pydantic import BaseModel, Field

from backend.domain.enums import VerificationStatus


class VerificationOtpRequest(BaseModel):
    method: str = Field(min_length=1)
    identifier: str = Field(min_length=1)


class VerificationOtpResponse(BaseModel):
    challenge_id: str
    masked_destination: str
    expires_in_seconds: int
    demo_otp: str | None = None


class VerificationRequest(BaseModel):
    challenge_id: str = Field(min_length=1)
    otp: str = Field(min_length=1)


class VerificationResponse(BaseModel):
    verification_id: str
    status: VerificationStatus
    patient_id: str | None = None
    existing_patient: bool = False
    visit_type: str
