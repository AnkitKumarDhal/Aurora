from datetime import datetime
from pydantic import Field
from domain.enums import AssignmentStatus
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
    collection_name = "doctor_assignments"
