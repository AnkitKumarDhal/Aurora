from datetime import datetime

from pydantic import BaseModel, Field


class ConsentRequest(BaseModel):
    version: str = Field(min_length=1)
    granted: bool
    method: str | None = None
    identifier: str | None = None


class ConsentResponse(BaseModel):
    version: str
    consent_status: str
    recorded_at: datetime


class ConsentInformationResponse(BaseModel):
    version: str
    status: str
    text: str
    audio_available: bool
    supported_languages: list[str]
