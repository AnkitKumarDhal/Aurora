from pydantic import BaseModel, Field


class PatientVerificationOtpRequest(BaseModel):
    draft_id: str = Field(min_length=1)
    method: str = Field(min_length=1)
    identifier: str = Field(min_length=1)


class PatientVerificationOtpResponse(BaseModel):
    challenge_id: str
    masked_destination: str
    expires_in_seconds: int
    demo_otp: str | None = None


class PatientVerificationOtpVerifyRequest(BaseModel):
    draft_id: str = Field(min_length=1)
    challenge_id: str = Field(min_length=1)
    otp: str = Field(min_length=1)


class PatientVerificationOtpVerifyResponse(BaseModel):
    verification_token: str
    status: str
    expires_in_seconds: int
