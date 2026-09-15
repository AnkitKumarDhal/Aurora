from datetime import datetime, timedelta, timezone

from backend.domain.enums import PromotionStatus
from backend.domain.promotion import PromotionRequest


def make_promotion_request() -> PromotionRequest:
    return PromotionRequest(
        promotion_request_id="promotion-001",
        queue_entry_id="queue-001",
        reason="Red flag requires priority review",
        decision_deadline=datetime.now(timezone.utc) + timedelta(seconds=60),
    )


def test_promotion_defaults_to_pending():
    request = make_promotion_request()

    assert request.status == PromotionStatus.PENDING
    assert request.decided_by is None
    assert request.decision_reason is None
    assert request.decided_at is None


def test_promotion_can_be_approved():
    request = make_promotion_request()

    request.status = PromotionStatus.APPROVED
    request.decided_by = "admin-001"
    request.decision_reason = "Approved by staff"
    request.decided_at = datetime.now(timezone.utc)

    assert request.status == PromotionStatus.APPROVED
    assert request.decided_by == "admin-001"
    assert request.decision_reason == "Approved by staff"
    assert request.decided_at is not None


def test_promotion_can_be_denied():
    request = make_promotion_request()

    request.status = PromotionStatus.DENIED
    request.decided_by = "admin-001"
    request.decision_reason = "Insufficient justification"
    request.decided_at = datetime.now(timezone.utc)

    assert request.status == PromotionStatus.DENIED
    assert request.decided_by == "admin-001"


def test_promotion_supports_auto_approval():
    request = make_promotion_request()
    request.status = PromotionStatus.AUTO_APPROVED

    assert request.status == PromotionStatus.AUTO_APPROVED


def test_promotion_supports_expiration():
    request = make_promotion_request()
    request.status = PromotionStatus.EXPIRED

    assert request.status == PromotionStatus.EXPIRED


def test_promotion_deadline_is_stored():
    deadline = datetime.now(timezone.utc) + timedelta(seconds=60)

    request = PromotionRequest(
        promotion_request_id="promotion-001",
        queue_entry_id="queue-001",
        reason="Urgent case",
        decision_deadline=deadline,
    )

    assert request.decision_deadline == deadline
