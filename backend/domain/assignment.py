from datetime import datetime
from .common import TimestampedModel
from .enums import AssignmentStatus


class DoctorAssignment(TimestampedModel):
    assignment_id: str
    session_id: str
    doctor_id: str
    department_id: str
    status: AssignmentStatus = AssignmentStatus.ACTIVE
    assigned_at: datetime | None = None
    released_at: datetime | None = None
