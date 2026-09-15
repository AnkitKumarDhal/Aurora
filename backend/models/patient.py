from datetime import date, datetime
from pydantic import Field
from .common import PersistenceModel


class PatientDocument(PersistenceModel):
    patient_id: str = Field(min_length=1)
    display_name: str
    date_of_birth: date | None = None
    age: int | None = Field(default=None, ge=0)
    abha_reference: str | None = None
    hospital_reference: str | None = None
    created_at: datetime
    updated_at: datetime
    collection_name = "patients"
