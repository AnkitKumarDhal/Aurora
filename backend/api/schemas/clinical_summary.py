from datetime import datetime
from pydantic import BaseModel, Field
from backend.domain.enums import SummaryStatus


class ClinicalSummaryCreateRequest(BaseModel):
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    relevant_documents: list[str] = Field(default_factory=list)
    clinical_signals: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None


class ClinicalSummaryUpdateRequest(BaseModel):
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: list[str] | None = None
    medications: list[str] | None = None
    allergies: list[str] | None = None
    relevant_documents: list[str] | None = None
    clinical_signals: list[str] | None = None
    generated_at: datetime | None = None
    status: SummaryStatus | None = None


class ClinicalSummaryResponse(BaseModel):
    summary_id: str
    session_id: str
    status: SummaryStatus
    chief_complaint: str | None
    history_of_present_illness: str | None
    past_medical_history: list[str]
    medications: list[str]
    allergies: list[str]
    relevant_documents: list[str]
    clinical_signals: list[str]
    generated_at: datetime | None
    confirmed_by: str | None
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime
