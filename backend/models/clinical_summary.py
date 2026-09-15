from datetime import datetime
from typing import ClassVar
from pydantic import Field
from domain.enums import SummaryStatus
from .common import PersistenceModel


class ClinicalSummaryDocument(PersistenceModel):
    summary_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
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
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "clinical_summaries"
