from datetime import datetime
from typing import ClassVar
from pydantic import Field
from backend.domain.enums import TriageStatus, UrgencyLevel
from .common import PersistenceModel


class TriageResultDocument(PersistenceModel):
    triage_result_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    urgency_level: UrgencyLevel | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    red_flags_present: bool = False
    status: TriageStatus = TriageStatus.PENDING
    assessed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "triage_results"
