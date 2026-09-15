from datetime import datetime
from pydantic import Field
from .common import TimestampedModel
from .enums import QueueStatus, UrgencyLevel


class QueueEntry(TimestampedModel):
    queue_entry_id: str
    session_id: str
    department_id: str
    status: QueueStatus = QueueStatus.WAITING
    position: int | None = Field(default=None, ge=1)
    urgency_level: UrgencyLevel | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    doctor_id: str | None = None
    queued_at: datetime | None = None
    called_at: datetime | None = None
    completed_at: datetime | None = None
