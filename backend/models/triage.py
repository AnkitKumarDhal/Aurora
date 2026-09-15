from datetime import datetime
from pydantic import Field
from domain.enums import TriageStatus, UrgencyLevel
from .common import PersistenceModel


class TriageResultDocument(PersistenceModel):
    triage_result_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    urgency_level: UrgencyLevel
    priority_score: int = Field(ge=0, le=100)
    red_flags_present: bool = False
    status: TriageStatus = TriageStatus.PENDING
    assessed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    collection_name = "triage_results"
