from datetime import datetime
from typing import ClassVar
from pydantic import Field
from domain.enums import ClinicalSignalType
from .common import PersistenceModel


class ClinicalSignalDocument(PersistenceModel):
    signal_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    signal_type: ClinicalSignalType
    name: str
    value: str | bool | int | float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "clinical_signals"
