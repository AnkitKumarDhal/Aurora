from datetime import datetime
from pydantic import BaseModel
from backend.api.schemas.queue import QueueEntryResponse
from backend.domain.enums import AssignmentStatus


class AssignmentResponse(BaseModel):
    assignment_id: str
    session_id: str
    doctor_id: str
    department_id: str
    status: AssignmentStatus
    assigned_at: datetime | None
    released_at: datetime | None


class WorkflowQueueResponse(BaseModel):
    queue_entry: QueueEntryResponse


class WorkflowAssignmentResponse(BaseModel):
    assignment: AssignmentResponse


class WorkflowQueueActionResponse(BaseModel):
    queue_entry: QueueEntryResponse
