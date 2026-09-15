import pytest
from pydantic import ValidationError

from backend.domain.enums import TriageStatus, UrgencyLevel
from backend.domain.triage import TriageResult


def make_triage_result() -> TriageResult:
    return TriageResult(
        triage_id="triage-001",
        session_id="session-001",
    )


def test_triage_defaults():
    result = make_triage_result()

    assert result.status == TriageStatus.PENDING
    assert result.urgency_level is None
    assert result.priority_score is None
    assert result.red_flags_present is False
    assert result.assessed_at is None


@pytest.mark.parametrize("urgency_level", list(UrgencyLevel))
def test_triage_accepts_valid_urgency_levels(urgency_level):
    result = TriageResult(
        triage_id="triage-001",
        session_id="session-001",
        urgency_level=urgency_level,
    )

    assert result.urgency_level == urgency_level


@pytest.mark.parametrize("priority_score", [0, 1, 50, 99, 100])
def test_triage_accepts_valid_priority_scores(priority_score):
    result = TriageResult(
        triage_id="triage-001",
        session_id="session-001",
        priority_score=priority_score,
    )

    assert result.priority_score == priority_score


@pytest.mark.parametrize("priority_score", [-1, 101])
def test_triage_rejects_invalid_priority_scores(priority_score):
    with pytest.raises(ValidationError):
        TriageResult(
            triage_id="triage-001",
            session_id="session-001",
            priority_score=priority_score,
        )


def test_triage_can_be_assessed():
    result = TriageResult(
        triage_id="triage-001",
        session_id="session-001",
        status=TriageStatus.ASSESSED,
        urgency_level=UrgencyLevel.LEVEL_2,
        priority_score=80,
        red_flags_present=True,
    )

    assert result.status == TriageStatus.ASSESSED
    assert result.urgency_level == UrgencyLevel.LEVEL_2
    assert result.priority_score == 80
    assert result.red_flags_present is True


def test_triage_can_fail():
    result = TriageResult(
        triage_id="triage-001",
        session_id="session-001",
        status=TriageStatus.FAILED,
    )

    assert result.status == TriageStatus.FAILED
