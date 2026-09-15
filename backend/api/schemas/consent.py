from datetime import datetime

from pydantic import BaseModel, Field

from backend.domain.enums import ConsentStatus


class ConsentRequest(BaseModel):
    version: str = Field(min_length=1)
    granted: bool


class ConsentResponse(BaseModel):
    version: str
    consent_status: ConsentStatus
    recorded_at: datetime


class ConsentInformationResponse(BaseModel):
    version: str
    status: ConsentStatus
    text: str
    audio_available: bool
    supported_languages: list[str]
