from datetime import datetime

from pydantic import BaseModel

from backend.api.schemas.clinical_summary import ClinicalSummaryResponse
from backend.domain.enums import QueueStatus, UrgencyLevel
from backend.domain.queue import QueueEntry


class DoctorQueuePatientResponse(BaseModel):
    patient_id: str
    display_name: str
    age: int | None


class DoctorQueueEntryResponse(BaseModel):
    queue_entry_id: str
    session_id: str
    position: int | None
    urgency_level: UrgencyLevel | None
    waiting_time_seconds: int | None
    doctor_id: str | None
    status: QueueStatus
    patient: DoctorQueuePatientResponse | None
    summary: ClinicalSummaryResponse | None
    queued_at: datetime | None
    called_at: datetime | None


class DoctorQueueResponse(BaseModel):
    entries: list[DoctorQueueEntryResponse]
