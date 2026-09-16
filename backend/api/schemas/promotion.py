from datetime import datetime
from pydantic import BaseModel, Field
from backend.domain.enums import PromotionStatus


class PromotionCreateRequest(BaseModel):
    queue_entry_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class PromotionDecisionRequest(BaseModel):
    decision_reason: str | None = None


class PromotionResponse(BaseModel):
    promotion_request_id: str
    queue_entry_id: str
    reason: str
    status: PromotionStatus
    decision_deadline: datetime
    decided_by: str | None
    decision_reason: str | None
    decided_at: datetime | None
