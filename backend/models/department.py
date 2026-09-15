from datetime import datetime
from typing import ClassVar
from pydantic import Field
from .common import PersistenceModel


class DepartmentDocument(PersistenceModel):
    department_id: str = Field(min_length=1)
    name: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "departments"
