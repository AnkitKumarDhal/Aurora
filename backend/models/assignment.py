from datetime import datetime
from typing import ClassVar
from pydantic import Field
from backend.domain.enums import AssignmentStatus
from .common import PersistenceModel


class DoctorAssignmentDocument(PersistenceModel):
    assignment_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    doctor_id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    status: AssignmentStatus = AssignmentStatus.ACTIVE
    assigned_at: datetime | None = None
    released_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "doctor_assignments"
