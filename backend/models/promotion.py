from datetime import datetime
from typing import ClassVar
from pydantic import Field
from backend.domain.enums import PromotionStatus
from .common import PersistenceModel


class PromotionRequestDocument(PersistenceModel):
    promotion_request_id: str = Field(min_length=1)
    queue_entry_id: str = Field(min_length=1)
    reason: str
    status: PromotionStatus = PromotionStatus.PENDING
    decision_deadline: datetime
    decided_by: str | None = None
    decision_reason: str | None = None
    decided_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    collection_name: ClassVar[str] = "promotion_requests"
