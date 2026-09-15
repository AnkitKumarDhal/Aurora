from datetime import datetime
from typing import ClassVar
from pydantic import Field
from domain.enums import ConsentStatus, SessionStatus, VerificationStatus
from .common import PersistenceModel


class ClinicalSessionDocument(PersistenceModel):
    session_id: str = Field(min_length=1)
    patient_id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    status: SessionStatus = SessionStatus.CREATED
    verification_status: VerificationStatus = VerificationStatus.PENDING
    consent_status: ConsentStatus = ConsentStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "clinical_sessions"
