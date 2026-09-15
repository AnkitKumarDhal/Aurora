from datetime import datetime
from pydantic import Field
from .common import TimestampedModel
from .enums import SummaryStatus


class ClinicalSummary(TimestampedModel):
    summary_id: str
    session_id: str
    status: SummaryStatus = SummaryStatus.GENERATING
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    relevant_documents: list[str] = Field(default_factory=list)
    clinical_signals: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
