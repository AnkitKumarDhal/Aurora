from pydantic import Field
from .common import TimestampedModel
from .enums import ClinicalSignalType


class ClinicalSignal(TimestampedModel):
    signal_id: str
    session_id: str
    signal_type: ClinicalSignalType
    name: str
    value: str | bool | int | float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str | None = None
