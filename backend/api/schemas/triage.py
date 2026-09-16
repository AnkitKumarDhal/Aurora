from datetime import datetime
from pydantic import BaseModel, Field
from backend.domain.enums import TriageStatus, UrgencyLevel


class TriageResponse(BaseModel):
    triage_id: str
    session_id: str
    status: TriageStatus
    urgency_level: UrgencyLevel | None
    priority_score: int | None
    red_flags_present: bool
    assessed_at: datetime | None


class TriageAssessRequest(BaseModel):
    trigger: str = Field(default="manual")
