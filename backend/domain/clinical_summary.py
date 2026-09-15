from datetime import datetime
from .common import TimestampedModel
from .enums import SummaryStatus


class ClinicalSummary(TimestampedModel):
    summary_id: str
    session_id: str
    status: SummaryStatus = SummaryStatus.GENERATING
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: list[str] = []
    medications: list[str] = []
    allergies: list[str] = []
    relevant_documents: list[str] = []
    clinical_signals: list[str] = []
    generated_at: datetime | None = None
    confirmed_by: str | None = None
    confirmed_at: str | None = None
