from datetime import datetime
from pydantic import BaseModel
from backend.domain.enums import ConsentStatus


class ConsentRequest(BaseModel):
    granted: bool


class ConsentResponse(BaseModel):
    consent_status: ConsentStatus
    recorded_at: datetime
