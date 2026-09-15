from pydantic import Field
from .common import TimestampedModel


class Doctor(TimestampedModel):
    doctor_id: str
    display_name: str

    department_ids: list[str] = Field(default_factory=list)
    available: bool = True
