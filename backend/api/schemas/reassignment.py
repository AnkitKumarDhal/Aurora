from pydantic import BaseModel, Field


class ReassignmentRequest(BaseModel):
    queue_entry_id: str = Field(
        min_length=1,
    )
    doctor_id: str = Field(
        min_length=1,
    )


class ReassignmentResponse(BaseModel):
    queue_entry_id: str
    session_id: str
    previous_doctor_id: str | None
    doctor_id: str
    assignment_id: str
