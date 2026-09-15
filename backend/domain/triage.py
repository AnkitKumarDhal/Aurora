from datetime import datetime
from pydantic import Field
from .common import TimestampedModel
from .enums import TriageStatus, UrgencyLevel


class TriageResult(TimestampedModel):
    triage_id: str
    session_id: str
    status: TriageStatus = TriageStatus.PENDING
    urgency_level: UrgencyLevel | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    red_flags_present: bool = False
    assessed_at: datetime | None = None
