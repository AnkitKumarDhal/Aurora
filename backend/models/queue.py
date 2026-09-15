from datetime import datetime
from typing import ClassVar
from pydantic import Field
from backend.domain.enums import QueueStatus, UrgencyLevel
from .common import PersistenceModel


class QueueEntryDocument(PersistenceModel):
    queue_entry_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    status: QueueStatus = QueueStatus.WAITING
    position: int | None = Field(default=None, ge=1)
    urgency_level: UrgencyLevel | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    doctor_id: str | None = None
    queued_at: datetime | None = None
    called_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "queue_entries"
