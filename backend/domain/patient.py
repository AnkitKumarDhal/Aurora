from datetime import datetime, date
from pydantic import Field
from .common import TimestampedModel


class Patient(TimestampedModel):
    patient_id: str
    display_name: str
    date_of_birth: date | None = None
    age: int | None = Field(default=None, ge=0)
    abha_reference: str | None = None
    aadhaar_reference: str | None = None
    hospital_reference: str | None = None
    storage_consent_granted_at: datetime | None = None
