from datetime import datetime
from pydantic import BaseModel
from backend.domain.enums import QueueStatus, UrgencyLevel


class QueueEntryResponse(BaseModel):
    queue_entry_id: str
    session_id: str
    department_id: str
    status: QueueStatus
    position: int | None
    urgency_level: UrgencyLevel | None
    priority_score: int | None
    doctor_id: str | None
    queued_at: datetime | None
    called_at: datetime | None
    completed_at: datetime | None
