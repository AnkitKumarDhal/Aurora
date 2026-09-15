from datetime import datetime
from typing import ClassVar
from pydantic import Field
from .common import PersistenceModel


class DoctorDocument(PersistenceModel):
    doctor_id: str = Field(min_length=1)
    display_name: str
    department_ids: list[str] = Field(default_factory=list)
    is_available: bool = True
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "doctors"
