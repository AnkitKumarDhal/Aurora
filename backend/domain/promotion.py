from datetime import datetime
from .common import TimestampedModel
from .enums import PromotionStatus


class PromotionRequest(TimestampedModel):
    promotion_request_id: str
    queue_entry_id: str
    target_doctor_id: str
    reason: str
    status: PromotionStatus = PromotionStatus.PENDING
    decision_deadline: datetime
    decided_by: str | None = None
    decision_reason: str | None = None
    decided_at: datetime | None = None
