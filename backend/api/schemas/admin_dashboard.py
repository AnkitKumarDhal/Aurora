from datetime import datetime

from pydantic import BaseModel

from backend.domain.enums import QueueStatus, UrgencyLevel


class AdminDashboardStats(BaseModel):
    patients: int
    waiting: int
    in_consultation: int
    doctors: int


class AdminDashboardDoctor(BaseModel):
    doctor_id: str
    display_name: str
    status: str
    assigned_count: int


class AdminDashboardPatient(BaseModel):
    queue_entry_id: str
    session_id: str
    patient_id: str
    display_name: str
    age: int | None
    urgency_level: UrgencyLevel | None
    priority_score: int | None
    queue_status: QueueStatus
    doctor_id: str | None
    doctor_name: str | None
    chief_complaint: str | None
    queued_at: datetime | None
    waiting_time_seconds: int | None


class AdminDashboardResponse(BaseModel):
    department_id: str
    stats: AdminDashboardStats
    doctors: list[AdminDashboardDoctor]
    patients: list[AdminDashboardPatient]
